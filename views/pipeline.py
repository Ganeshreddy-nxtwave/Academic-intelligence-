"""Pipeline page — the entire flow, raw exports through to the dashboard pages.

Shows the end-to-end flow (raw exports -> build scripts -> canonical -> DuckDB ->
agent -> the 3 pages), live row counts per table/view, and the per-course content
inventory. Visualises the current committed state; it does not re-run ingestion
(raw files are gitignored and absent on Streamlit Cloud).
"""
import streamlit as st

from aip import dashboard

# What each build script produces -> which tables. Raw files aren't present on Cloud,
# so this manifest documents the sources; counts come from the live DB.
STAGES = [
    ("build_operational.py", "Clickup scheduling + feedback (xlsx)", ["sessions", "session_feedback", "instructor_sessions"]),
    ("build_delivered.py",   "Clickup scheduled sessions (csv)",     ["delivered_sessions", "delivered_niat"]),
    ("build_designed.py",    "HLID + Prod Sequence (xlsx)",          ["designed_sequence", "designed_course_plan"]),
    ("build_content.py",     "Course content exports (xlsx/json)",   ["course_content"]),
    ("build_issues.py",      "RCA / issues board (xlsx)",            ["issues"]),
    ("build_subject_tags.py", "1st-Year Subjects sheet (xlsx)",      ["subject_tags"]),
    ("build_course_crosswalk.py", "Catalogue + delivered names",     ["course_crosswalk"]),
    ("(committed reference)", "tag → content-course map",            ["tag_content_map"]),
]

DOT = """
digraph pipeline {
  rankdir=LR; bgcolor="transparent";
  node [shape=box style="rounded,filled" fontname="Helvetica" fontsize=11 color="#d0d0d0"];
  raw   [label="Raw exports\\nxlsx · json · csv" fillcolor="#fff3e0"];
  build [label="build_*.py\\n(7 ingestion scripts)" fillcolor="#f5f5f7"];
  canon [label="Canonical\\nCSV · parquet\\n(committed)" fillcolor="#f5f5f7"];
  duck  [label="load_duckdb.py\\ntables + views" fillcolor="#e3f2fd"];
  agent [label="Copilot agent\\nread-only SQL\\n+ OpenRouter" fillcolor="#e8f5e9"];
  pages [label="Dashboard\\nChat · Knowledge Base · Pipeline" fillcolor="#ede7f6"];
  raw -> build -> canon -> duck -> agent -> pages;
  duck -> pages [style=dashed label="direct reads"];
}
"""


def render():
    st.title("🔧 Pipeline")
    st.caption("The entire flow — raw exports through to the dashboard. Rebuilt from "
               "committed data on every deploy; this reflects the current state.")

    try:
        st.graphviz_chart(DOT, width="stretch")
    except Exception:  # noqa: BLE001 - fall back to a plain stage strip if graphviz is unavailable
        cols = st.columns(6)
        for c, label in zip(cols, ["Raw exports", "build_*.py", "Canonical files",
                                   "DuckDB", "Agent", "Dashboard pages"]):
            c.info(label)

    counts = dict(dashboard.table_counts())
    con = dashboard.conn()

    total_rows = sum(counts.values())
    k = st.columns(4)
    k[0].metric("Ingestion scripts", len(STAGES))
    k[1].metric("Tables + views", len(counts))
    k[2].metric("Total rows", f"{total_rows:,}")
    k[3].metric("Courses w/ content",
                con.execute("SELECT count(DISTINCT course) FROM course_content").fetchone()[0])

    st.subheader("Sources → tables")
    st.dataframe(
        [{"Build script": s, "Source": src,
          "Produces": ", ".join(t), "Rows": f"{sum(counts.get(t2, 0) for t2 in t):,}"}
         for s, src, t in STAGES],
        width="stretch", hide_index=True)

    st.subheader("DuckDB tables & views")
    views = {r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_type='VIEW'").fetchall()}
    st.dataframe(
        [{"Name": n, "Kind": "view" if n in views else "table", "Rows": f"{c:,}"}
         for n, c in sorted(counts.items())],
        width="stretch", hide_index=True)

    st.subheader("Content ingested (per course)")
    inv = con.execute("""SELECT course,
            count(*) FILTER (WHERE kind='reading')        AS readings,
            count(*) FILTER (WHERE kind='objective')      AS objective,
            count(*) FILTER (WHERE kind='classroom_quiz') AS classroom_quiz,
            count(*) FILTER (WHERE kind='coding')         AS coding,
            count(*) AS total
        FROM course_content GROUP BY 1 ORDER BY total DESC""").fetchall()
    st.dataframe(
        [{"Course": r[0], "Readings": r[1], "Objective": r[2],
          "Classroom quiz": r[3], "Coding": r[4], "Total": r[5]} for r in inv],
        width="stretch", hide_index=True)
    st.caption(f"{len(inv)} courses ingested. Raw source files are gitignored; this "
               "reflects the committed state — it updates when new data is committed and redeployed.")
