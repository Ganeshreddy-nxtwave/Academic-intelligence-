"""Knowledge Base page — per-university catalog of everything the system knows.

Pick a university (clickable grid) -> its delivery overview, its subjects with the
university's local name mapped to the NxtWave tag (subject_tags crosswalk), the
content actually delivered there (joined by unit_id, drillable), its feedback,
recorded issues, and designed plan. All read-only over existing tables/views.
"""
import streamlit as st

from aip import dashboard


def _uni_grid(colleges):
    """Clickable grid of universities (pills) — all visible, selected one highlighted.
    Returns the selected institute_name."""
    if "kb_uni" not in st.session_state or st.session_state.kb_uni not in colleges:
        st.session_state.kb_uni = colleges[0]
    per_row = 4
    for i in range(0, len(colleges), per_row):
        cols = st.columns(per_row)
        for col, name in zip(cols, colleges[i:i + per_row]):
            selected = name == st.session_state.kb_uni
            if col.button(name, key=f"uni::{name}", width="stretch",
                          type="primary" if selected else "secondary"):
                st.session_state.kb_uni = name
                st.rerun()
    return st.session_state.kb_uni


def render():
    st.title("📚 Knowledge Base")
    st.caption("Everything the copilot draws on for a university — its subjects "
               "(their names ↔ ours), delivered content, feedback, issues, and plan.")
    con = dashboard.conn()

    colleges = [r[0] for r in con.execute(
        "SELECT institute_name FROM college_summary ORDER BY 1").fetchall()]
    if not colleges:
        st.info("No colleges with delivery data found.")
        return
    uni = _uni_grid(colleges)
    st.divider()
    st.subheader(uni)

    # --- overview ---
    row = con.execute("""SELECT sections, courses, scheduled_sessions, pct_completed,
            teaching_weeks, avg_understanding, avg_teaching, recorded_issues, has_designed_plan
        FROM college_summary WHERE institute_name = ?""", [uni]).fetchone()
    if row:
        sec, crs, sess, comp, wks, und, tea, iss, plan = row
        m = st.columns(6)
        m[0].metric("Courses", crs)
        m[1].metric("Sessions", f"{sess:,}" if sess else "0")
        m[2].metric("Completion", f"{comp:.0f}%" if comp is not None else "—")
        m[3].metric("Understanding", f"{und}" if und is not None else "—")
        m[4].metric("Teaching", f"{tea}" if tea is not None else "—")
        m[5].metric("Issues", iss)
        st.caption(f"{sec} section(s) · {wks} teaching weeks · "
                   f"{'has a designed plan' if plan else 'no designed plan on file'}")

    tab_subjects, tab_content, tab_fb, tab_issues, tab_plan = st.tabs(
        ["Subjects", "Content", "Feedback", "Issues", "Plan"])

    # --- SUBJECTS: the crosswalk — their name vs the NxtWave tag ---
    with tab_subjects:
        subs = con.execute("""SELECT semester, university_course, nxtwave_tag, credits, course_id
            FROM subject_tags WHERE institute_name = ?
            ORDER BY semester, university_course""", [uni]).fetchall()
        if subs:
            st.markdown("**This university's subjects, mapped to the NxtWave standard**")
            st.dataframe(
                [{"Semester": r[0], "Their course name": r[1], "NxtWave tag": r[2],
                  "Credits": r[3], "Course ID": r[4]} for r in subs],
                width="stretch", hide_index=True)
        else:
            st.info("No subject-tag mapping on file for this university.")

    # --- CONTENT: what content (by unit_id) was actually delivered here ---
    with tab_content:
        pivot = con.execute("""
            WITH du AS (SELECT DISTINCT unit_id FROM delivered_sessions
                        WHERE institute_name = ? AND unit_id IS NOT NULL)
            SELECT ca.course AS course,
                   count(*) FILTER (WHERE ca.kind='reading')        AS readings,
                   count(*) FILTER (WHERE ca.kind='objective')      AS objective,
                   count(*) FILTER (WHERE ca.kind='classroom_quiz') AS classroom_quiz,
                   count(*) FILTER (WHERE ca.kind='coding')         AS coding,
                   count(*) AS total
            FROM content_all ca JOIN du USING (unit_id)
            GROUP BY 1 ORDER BY total DESC""", [uni]).fetchall()
        st.markdown("**Content delivered here** (matched by unit — what students "
                    "at this university actually saw)")
        if pivot:
            st.dataframe(
                [{"Course": r[0], "Readings": r[1], "Objective": r[2],
                  "Classroom quiz": r[3], "Coding": r[4], "Total units": r[5]} for r in pivot],
                width="stretch", hide_index=True)
        else:
            st.info("No ingested content matched this university's delivered units yet.")

        courses_with_content = [r[0] for r in con.execute(
            "SELECT DISTINCT course FROM course_content ORDER BY 1").fetchall()]
        if courses_with_content:
            st.markdown("**Browse a course's content**")
            course = st.selectbox("Course", courses_with_content, key="kb_course")
            total = con.execute("SELECT count(*) FROM course_content WHERE course = ?",
                                [course]).fetchone()[0]
            rows = con.execute("""SELECT kind, difficulty, content, options, correct_answer
                FROM course_content WHERE course = ? ORDER BY kind LIMIT 100""",
                [course]).fetchall()
            st.caption(f"{total:,} units in {course} — showing first {len(rows)}")
            st.dataframe(
                [{"Kind": r[0], "Difficulty": r[1] or "", "Content": (r[2] or "")[:300],
                  "Options": (r[3] or "")[:200], "Answer": (r[4] or "")[:120]} for r in rows],
                width="stretch", hide_index=True)

    # --- FEEDBACK ---
    with tab_fb:
        agg = con.execute("""SELECT count(*), sum(TRY_CAST(total_feedbacks AS INT)),
                round(avg(TRY_CAST(session_understanding_rating AS DOUBLE)),2),
                round(avg(TRY_CAST(teaching_quality_rating AS DOUBLE)),2)
            FROM session_feedback_safe WHERE institute_name = ?""", [uni]).fetchone()
        if agg and agg[0]:
            f = st.columns(3)
            f[0].metric("Rated sessions", f"{agg[0]:,}")
            f[1].metric("Avg understanding", agg[2])
            f[2].metric("Avg teaching", agg[3])
            low = con.execute("""SELECT session_title, teaching_quality_rating, total_feedbacks
                FROM session_feedback_safe WHERE institute_name = ?
                AND TRY_CAST(teaching_quality_rating AS DOUBLE) IS NOT NULL
                ORDER BY TRY_CAST(teaching_quality_rating AS DOUBLE) LIMIT 10""", [uni]).fetchall()
            st.markdown("**Lowest-rated sessions (teaching quality)**")
            st.dataframe([{"Session": r[0], "Teaching": r[1], "Feedbacks": r[2]} for r in low],
                         width="stretch", hide_index=True)
        else:
            st.info("No feedback recorded for this university.")

    # --- ISSUES ---
    with tab_issues:
        issues = con.execute("""SELECT primary_layer, category, issue_title,
                solutioning_direction, status
            FROM issues WHERE institute_name = ? ORDER BY primary_layer""", [uni]).fetchall()
        if issues:
            st.caption(f"{len(issues)} recorded issue(s)")
            st.dataframe(
                [{"Layer": r[0], "Category": r[1], "Issue": r[2],
                  "Solutioning direction": r[3], "Status": r[4]} for r in issues],
                width="stretch", hide_index=True)
        else:
            st.info("No recorded issues for this university "
                    "(issues are logged mainly for Aurora / MRV / CDU).")

    # --- PLAN ---
    with tab_plan:
        plan_rows = con.execute("""SELECT course, planned_sessions, actual_lectures_per_section,
                planned_total_hours, planned_weeks, coverage
            FROM course_plan_vs_actual
            WHERE university IN (SELECT code FROM universities WHERE institute_name = ?)
            ORDER BY planned_sessions DESC NULLS LAST""", [uni]).fetchall()
        if plan_rows:
            st.dataframe(
                [{"Course": r[0], "Planned sessions": r[1], "Actual/section": r[2],
                  "Planned hrs": r[3], "Planned weeks": r[4], "Coverage": r[5]} for r in plan_rows],
                width="stretch", hide_index=True)
        else:
            st.info("No designed plan on file — only MRV, Yenepoya, SGU, and CDU have one.")
