#!/usr/bin/env python3
"""Assemble data/aip.duckdb from the git-committed canonical files + courses.csv.

No raw data needed — this is what makes the repo self-sufficient: a fresh clone
(or a Streamlit Cloud deploy, which only ever sees git) can rebuild the queryable
store from what's committed.

Views exist to pre-solve joins a caller would otherwise get wrong. That is the
whole point of them: `deviation` in particular encodes the trickiest join in the
store so nobody re-derives it per question.

Usage: python scripts/load_duckdb.py
"""
import duckdb, glob, os, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def build(db="data/aip.duckdb", verbose=True):
    if os.path.exists(db):
        os.remove(db)
    con = duckdb.connect(db)

    sources = [("courses", "data/courses.csv")]
    for p in sorted(glob.glob("data/canonical/*.csv")) + sorted(glob.glob("data/canonical/*.parquet")):
        sources.append((os.path.splitext(os.path.basename(p))[0], p))
    for name, path in sources:
        p = path.replace(os.sep, "/")
        reader = (f"read_parquet('{p}')" if p.endswith(".parquet")
                  else f"read_csv_auto('{p}', header=true, all_varchar=true)")
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM {reader}")

    # --- views ---

    # content_units: unified view over the three content-item tables.
    con.execute("""CREATE VIEW content_units AS
        SELECT unit_id, course_title, 'objective' AS k FROM objective_questions
        UNION ALL SELECT unit_id, course_title, 'coding'  FROM coding_questions
        UNION ALL SELECT unit_id, course_title, 'reading' FROM reading_materials""")

    # session_feedback_safe: ratings + counts, WITHOUT the student comment text.
    # The agent is pointed here, never at the base table — the app deploys from a
    # repo to third-party infra and free-text student complaints must not leave.
    con.execute("""CREATE VIEW session_feedback_safe AS
        SELECT institute_name, session_id, session_title, unit_ids,
               total_feedbacks, session_understanding_rating, teaching_quality_rating
        FROM session_feedback""")

    # delivered_sections: delivered_sessions.batch_section_name is a COMMA-SEPARATED
    # LIST ("TU Batch-1-S-002, TU Batch-1-S-003"), so one row covers several sections.
    # Counting it raw counts section-groupings, not sections. This explodes it.
    con.execute("""CREATE VIEW delivered_sections AS
        SELECT d.institute_name, d.semester, d.session_id, d.unit_id,
               d.session_type, d.start_ts, trim(s.section) AS section
        FROM delivered_sessions d,
             unnest(string_split(d.batch_section_name, ',')) AS s(section)
        WHERE trim(s.section) <> ''""")

    # deviation: designed vs delivered, per university, on unit_id — the hardest join
    # in the store, encoded once. Semester 1 only: designed data covers Sem 1 only.
    con.execute("""CREATE VIEW deviation AS
        WITH d AS (
            SELECT ds.university,
                   u.institute_name,
                   ds.unit_id,
                   any_value(ds.course)        AS course,
                   min(ds.planned_start)       AS planned_start
            FROM designed_sequence ds
            JOIN universities u ON u.code = ds.university
            WHERE ds.unit_id IS NOT NULL AND ds.unit_id <> ''
            GROUP BY 1, 2, 3
        ),
        v AS (
            -- ONLY institutes that have designed data on file. Without this, delivered
            -- units at the other 14 institutes get labelled 'added' when the truth is
            -- simply that no design exists to compare against.
            SELECT institute_name, unit_id, min(start_ts) AS actual_start
            FROM delivered_sessions
            WHERE semester = 'Semester 1'
              AND institute_name IN (SELECT institute_name FROM universities)
            GROUP BY 1, 2
        )
        SELECT
            coalesce(d.university, u2.code)            AS university,
            coalesce(d.institute_name, v.institute_name) AS institute_name,
            d.course,
            coalesce(d.unit_id, v.unit_id)             AS unit_id,
            try_cast(d.planned_start AS DATE)          AS planned_start,
            v.actual_start,
            date_diff('day', try_cast(d.planned_start AS DATE), v.actual_start) AS drift_days,
            CASE WHEN d.unit_id IS NOT NULL AND v.unit_id IS NOT NULL THEN 'delivered'
                 WHEN d.unit_id IS NOT NULL THEN 'dropped'
                 ELSE 'added' END                      AS status
        FROM d
        FULL OUTER JOIN v
          ON d.unit_id = v.unit_id AND d.institute_name = v.institute_name
        LEFT JOIN universities u2 ON u2.institute_name = v.institute_name""")

    if verbose:
        print("=== aip.duckdb (from committed canonical) ===")
        for (t,) in con.execute("SHOW TABLES").fetchall():
            n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            print(f"  {t}: {n} rows")

    tables = [t for (t,) in con.execute("SHOW TABLES").fetchall()]
    assert "courses" in tables and len(tables) > 1, "no canonical tables loaded"
    con.close()
    return db


if __name__ == "__main__":
    build()
