"""Academic Intelligence Platform — chat over the academic data store.

Run locally:  streamlit run app.py
Deploy:       Streamlit Cloud, with secrets OPENROUTER_API_KEY / AIP_MODEL /
              AIP_SHEET_ID / GOOGLE_SERVICE_ACCOUNT_JSON.
"""
import os
import pathlib

import streamlit as st

from aip import agent, db, feedback

st.set_page_config(page_title="Academic Intelligence", page_icon="🎓", layout="wide")


def secret(name, default=None):
    """Streamlit Cloud secrets, falling back to env for local runs."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:  # noqa: BLE001 - no secrets.toml locally is fine
        pass
    return os.environ.get(name, default)


@st.cache_resource
def get_db():
    """Build aip.duckdb from committed data if absent.

    Streamlit Cloud only ever sees git, and aip.duckdb is gitignored — so on a
    fresh deploy it must be rebuilt from the committed canonical files.
    """
    if not pathlib.Path(db.DB_PATH).exists():
        import scripts.load_duckdb as loader
        loader.build(db.DB_PATH, verbose=False)
    return db.connect()


con = get_db()
MODEL = secret("AIP_MODEL", agent.DEFAULT_MODEL)
API_KEY = secret("OPENROUTER_API_KEY")

if "msgs" not in st.session_state:
    st.session_state.msgs = []   # [{role, content, sql?, question?, fb_done?}]


def render_feedback(i, m):
    """Per-response feedback: 👍/👎 + 'what could be improved'. One log row per answer."""
    if m.get("fb_done"):
        st.caption(f"✅ {m['fb_done']}")
        return
    with st.form(key=f"fb_{i}"):
        improvement = st.text_input(
            "What could be improved?",
            placeholder="Optional — e.g. 'should exclude BREAK sessions', 'wrong course mapping'",
        )
        c1, c2, c3 = st.columns([1, 1, 8])
        up = c1.form_submit_button("👍")
        down = c2.form_submit_button("👎")
        send = c3.form_submit_button("Submit")
    if up or down or send:
        ok, msg = feedback.log(
            question=m.get("question", ""),
            sql=m.get("sql", []),
            answer=m["content"],
            verdict="up" if up else "down" if down else "",
            improvement=improvement,
            model=MODEL,
            sheet_id=secret("AIP_SHEET_ID"),
            sa_json=secret("GOOGLE_SERVICE_ACCOUNT_JSON"),
        )
        st.session_state.msgs[i]["fb_done"] = msg
        st.rerun()


with st.sidebar:
    st.subheader("Academic Intelligence")
    st.caption("Ask anything the data can answer — content, courses, delivery, "
               "feedback, instructors, plan-vs-actual.")
    st.write(f"**Model:** `{MODEL}`")
    tables = [t for (t,) in con.execute("SHOW TABLES").fetchall()]
    with st.expander(f"Data ({len(tables)} tables)"):
        for t in tables:
            n = con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
            st.write(f"`{t}` — {n:,}")
    if not secret("AIP_SHEET_ID"):
        st.warning("No feedback Sheet configured — feedback saves locally and "
                   "will not persist on Cloud.", icon="⚠️")
    if st.button("Clear chat"):
        st.session_state.msgs = []
        st.rerun()

st.title("🎓 Academic Intelligence")

if not API_KEY:
    st.error("No `OPENROUTER_API_KEY` set. Add it to `.streamlit/secrets.toml` "
             "locally, or to Secrets on Streamlit Cloud.")
    st.stop()

if not st.session_state.msgs:
    st.caption("Try: *“Which instructors have the lowest completion rate?”* · "
               "*“How many coding questions exist per course?”* · "
               "*“Which MRV units were delivered late vs the plan?”*")

# --- history ---
for i, m in enumerate(st.session_state.msgs):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            if m.get("sql"):
                with st.expander(f"Show SQL ({len(m['sql'])} quer{'y' if len(m['sql']) == 1 else 'ies'})"):
                    for q in m["sql"]:
                        st.code(q, language="sql")
            render_feedback(i, m)

# --- input ---
if q := st.chat_input("Ask about the academic data…"):
    st.session_state.msgs.append({"role": "user", "content": q})
    history = [{"role": m["role"], "content": m["content"]}
               for m in st.session_state.msgs[:-1] if m["role"] in ("user", "assistant")]
    with st.chat_message("user"):
        st.markdown(q)
    with st.chat_message("assistant"), st.spinner("Querying the data…"):
        try:
            text, trace = agent.answer(q, history=history, api_key=API_KEY, model=MODEL, con=con)
        except agent.OpenRouterError as e:
            text, trace = f"❌ Could not reach the model: {e}", []
    st.session_state.msgs.append(
        {"role": "assistant", "content": text, "sql": trace, "question": q}
    )
    st.rerun()
