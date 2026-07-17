"""OpenRouter tool-calling agent: answers questions by querying DuckDB read-only.

One tool (run_sql) covers every question shape — analytics are aggregations,
content lookup is a select, advisory is query-then-reason. The prompt is
deliberately schema-heavy and instruction-light: breadth of coverage comes from
the agent knowing the data, not from task-specific prompting.
"""
import json
import os
import pathlib
import time

import requests

from . import db

API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-sonnet-4.5"
MAX_TOOL_ITERS = 5
NOTES_PATH = pathlib.Path(__file__).resolve().parents[1] / "docs" / "data-notes.md"

TOOLS = [{
    "type": "function",
    "function": {
        "name": "run_sql",
        "description": (
            "Run a read-only SQL query (DuckDB dialect) against the academic data store "
            "and get rows back. Only SELECT/WITH is permitted. Use this for every factual "
            "claim — never state a number that did not come from a query."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "A single DuckDB SELECT/WITH statement."}
            },
            "required": ["query"],
        },
    },
}]


def _notes() -> str:
    try:
        return NOTES_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def system_prompt(con=None) -> str:
    return f"""You answer questions about NxtWave's academic data (NIAT programme) for the Gen-AI Content team.

You have one tool: `run_sql`, a read-only DuckDB query. Every factual claim you make must come from a query you actually ran. If you did not query it, do not assert it.

## Live database schema
{db.schema_text(con)}

## Data notes (authoritative — these override any assumption)
{_notes()}

## How to work
- Explore with small queries first if you are unsure of values (e.g. `SELECT DISTINCT ...`).
- Prefer the pre-built views (`deviation`, `delivered_sections`, `session_feedback_safe`, `content_units`) over re-deriving their joins.
- If a query returns nothing, say so — do not substitute a different question's answer.
- If the data cannot answer the question, say that plainly and explain what is missing.

## Every answer must show its reasoning
A bare number is not an acceptable answer — the reader must be able to judge whether to trust it. Structure every response as:

1. **The answer**, lead with it, in plain language.
2. **How you got it** — which tables/views you queried, what you filtered on, and what each number actually counts (e.g. "distinct unit_id, Semester 1 only, sections exploded"). Name the real tables you used.
3. **What affects it** — assumptions you made, and any caveat from the data notes that materially changes how the number should be read. If a caveat applies, state it next to the number, not as a footnote.

Be concise: this is 2-4 sentences of reasoning for a simple question, not an essay. But never skip step 2.

Rules that override brevity:
- Never state a number that did not come from a query you ran.
- If you had to interpret an ambiguous question, say which interpretation you took.
- If the result rests on a known-weak join or partial data (e.g. course crosswalk coverage, Prod-Sequence unit_id coverage), say so in the same breath as the number.
- Distinguish "the data says zero" from "the data does not cover this". They are different answers.
"""


class OpenRouterError(Exception):
    pass


def _post(payload, api_key, retries=3):
    last = None
    for attempt in range(retries):
        try:
            r = requests.post(
                API_URL,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=120,
            )
            if r.status_code == 200:
                return r.json()
            last = f"{r.status_code}: {r.text[:300]}"
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)   # transient — back off and retry
                continue
            raise OpenRouterError(last)   # 4xx: retrying will not help
        except requests.RequestException as e:
            last = str(e)
            time.sleep(2 ** attempt)
    raise OpenRouterError(f"OpenRouter unavailable after {retries} attempts: {last}")


def answer(question, history=None, api_key=None, model=None, con=None):
    """Answer a question. Returns (text, sql_trace).

    sql_trace is the list of queries actually run, so the UI can show its working
    and the feedback log can record exactly what produced the answer.
    """
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterError("No OPENROUTER_API_KEY configured.")
    model = model or os.environ.get("AIP_MODEL", DEFAULT_MODEL)
    own = con is None
    con = con or db.connect()

    messages = [{"role": "system", "content": system_prompt(con)}]
    for turn in (history or []):
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": question})

    sql_trace = []
    try:
        for _ in range(MAX_TOOL_ITERS):
            data = _post({"model": model, "messages": messages, "tools": TOOLS}, api_key)
            msg = data["choices"][0]["message"]
            messages.append(msg)
            calls = msg.get("tool_calls") or []
            if not calls:
                return (msg.get("content") or "").strip(), sql_trace

            for call in calls:
                try:
                    query = json.loads(call["function"]["arguments"])["query"]
                except (KeyError, ValueError) as e:
                    content = f"Could not parse tool arguments: {e}"
                    query = None
                if query is not None:
                    sql_trace.append(query)
                    try:
                        cols, rows, truncated = db.run_sql(query, con)
                        content = _format(cols, rows, truncated)
                    except db.QueryError as e:
                        # Feed the error back verbatim so the model can repair it.
                        content = f"ERROR: {e}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": content,
                })

        # Iteration cap hit: answer with what we have rather than looping forever.
        data = _post({"model": model, "messages": messages + [{
            "role": "user",
            "content": "Answer now with what you have. Say explicitly that the investigation was truncated.",
        }]}, api_key)
        return (data["choices"][0]["message"].get("content") or "").strip(), sql_trace
    finally:
        if own:
            con.close()


def _format(cols, rows, truncated):
    if not rows:
        return "0 rows."
    head = " | ".join(cols)
    body = "\n".join(" | ".join("" if v is None else str(v) for v in r) for r in rows[:200])
    note = f"\n({len(rows)} rows" + (f", TRUNCATED at {db.ROW_LIMIT}" if truncated else "") + ")"
    if len(rows) > 200:
        note += " [showing first 200]"
    return f"{head}\n{body}{note}"
