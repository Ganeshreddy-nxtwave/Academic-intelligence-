"""Academic Intelligence Platform — chat over the academic data store.

Run locally:  streamlit run app.py
Deploy:       Streamlit Cloud, with secrets OPENROUTER_API_KEY / AIP_MODEL.
"""
import os

import streamlit as st

from aip import agent, db

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
    """Rebuild aip.duckdb from committed data on every boot, then connect read-only.

    ALWAYS rebuild — do not skip when the file exists. Streamlit Cloud keeps the
    container filesystem across restarts, so a "build only if missing" check served a
    database built by older code forever: new tables and views shipped in git simply
    never appeared, with no error to notice. The rebuild takes ~2.6s from the committed
    parquet/CSVs and @st.cache_resource means it runs once per boot. Correctness is
    worth 2.6s.
    """
    import scripts.load_duckdb as loader
    loader.build(db.DB_PATH, verbose=False)
    return db.connect()


con = get_db()
API_KEY = secret("OPENROUTER_API_KEY")

# Cost/capability ladder, cheapest first — the slider order. All three support
# tool-calling (verified against OpenRouter's live list), which this agent requires.
# Prices are input/output per million tokens.
MODEL_TIERS = [
    ("Haiku",  "anthropic/claude-haiku-4.5",  "$1/$5 · fastest, cheapest — counts and lookups"),
    ("Sonnet", "anthropic/claude-sonnet-4.5", "$3/$15 · balanced — most questions"),
    ("Opus",   "anthropic/claude-opus-4.8",   "$5/$25 · deepest analysis — planning, HLIDs, advisory"),
]
TIER_MODEL = {name: model for name, model, _ in MODEL_TIERS}
TIER_NOTE = {name: note for name, _, note in MODEL_TIERS}

if "msgs" not in st.session_state:
    st.session_state.msgs = []   # [{role, content}]

with st.sidebar:
    st.subheader("Academic Intelligence")
    st.caption("Ask anything the data can answer — content, courses, delivery, "
               "feedback, instructors, plan-vs-actual.")

    # AIP_MODEL picks where the slider starts; the slider is the control from then on.
    configured = secret("AIP_MODEL", agent.DEFAULT_MODEL)
    start = next((n for n, m, _ in MODEL_TIERS if m == configured), "Opus")
    tier = st.select_slider(
        "Model",
        options=[n for n, _, _ in MODEL_TIERS],
        value=start,
        help="Slide right for deeper analysis, left for speed and lower cost.",
    )
    MODEL = TIER_MODEL[tier]
    st.caption(TIER_NOTE[tier])
    if tier == "Haiku":
        st.caption("⚠️ Haiku is fine for lookups but weaker on multi-step "
                   "analysis — use Opus for planning questions.")

    tables = [t for (t,) in con.execute("SHOW TABLES").fetchall()]
    with st.expander(f"Data ({len(tables)} tables)"):
        for t in tables:
            n = con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
            st.write(f"`{t}` — {n:,}")
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

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if q := st.chat_input("Ask about the academic data…"):
    st.session_state.msgs.append({"role": "user", "content": q})
    history = [{"role": m["role"], "content": m["content"]}
               for m in st.session_state.msgs[:-1]]
    with st.chat_message("user"):
        st.markdown(q)
    with st.chat_message("assistant"), st.spinner("Querying the data…"):
        try:
            text, _ = agent.answer(q, history=history, api_key=API_KEY, model=MODEL, con=con)
        except agent.OpenRouterError as e:
            text = f"❌ Could not reach the model: {e}"
    st.session_state.msgs.append({"role": "assistant", "content": text})
    st.rerun()
