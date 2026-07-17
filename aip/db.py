"""Read-only DuckDB access for the chat agent, plus live schema introspection.

The SQL here is model-generated text crossing a trust boundary, so the guardrail
is engine-enforced (a read_only connection), not just string matching. The string
checks are a second layer, not the primary one.
"""
import os
import re
import threading

import duckdb

DB_PATH = os.environ.get("AIP_DB", "data/aip.duckdb")
ROW_LIMIT = 1000
TIMEOUT_S = 20

# Second layer only — the read_only connection is what actually enforces this.
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|create|alter|attach|detach|copy|install|load|"
    r"export|import|pragma|set|call|checkpoint)\b",
    re.IGNORECASE,
)


class QueryError(Exception):
    """Raised for a rejected or failed query. The message is shown to the model."""


def connect(path: str = None):
    """Read-only connection. Writes fail at the engine, regardless of the SQL."""
    return duckdb.connect(path or DB_PATH, read_only=True)


def _validate(sql: str) -> str:
    s = sql.strip().rstrip(";").strip()
    if not s:
        raise QueryError("Empty query.")
    # Reject multi-statement outright: only one statement may run.
    if ";" in s:
        raise QueryError("Only a single statement is allowed; remove the ';'.")
    if not re.match(r"^\s*(select|with)\b", s, re.IGNORECASE):
        raise QueryError("Only SELECT/WITH queries are allowed.")
    hit = _FORBIDDEN.search(s)
    if hit:
        raise QueryError(f"'{hit.group(0)}' is not allowed. This connection is read-only.")
    return s


def run_sql(sql: str, con=None):
    """Execute a read-only query. Returns (columns, rows, truncated).

    Raises QueryError on rejection, timeout, or SQL error — the caller feeds the
    message back to the model so it can repair, rather than guessing an answer.
    """
    s = _validate(sql)
    own = con is None
    con = con or connect()
    result = {}

    def _run():
        try:
            cur = con.execute(s)
            result["cols"] = [d[0] for d in cur.description] if cur.description else []
            result["rows"] = cur.fetchmany(ROW_LIMIT + 1)
        except Exception as e:  # noqa: BLE001 - surfaced to the model verbatim
            result["err"] = str(e)

    # ponytail: DuckDB has no statement_timeout, so interrupt from a watchdog thread.
    # A cross join over delivered_sessions (239K rows) would otherwise hang the app.
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(TIMEOUT_S)
    if t.is_alive():
        con.interrupt()
        t.join(2)
        raise QueryError(f"Query exceeded {TIMEOUT_S}s and was cancelled. Narrow it (filter or aggregate).")

    if "err" in result:
        raise QueryError(f"SQL error: {result['err']}")

    rows = result.get("rows", [])
    truncated = len(rows) > ROW_LIMIT
    if own:
        con.close()
    return result.get("cols", []), rows[:ROW_LIMIT], truncated


def schema_text(con=None) -> str:
    """Dump the live schema: every table/view with its columns and types.

    Introspected at runtime rather than maintained in a file, so it cannot drift
    from the actual database. Capability is bounded by what the agent knows about
    the schema, so this is the highest-value part of the prompt.
    """
    own = con is None
    con = con or connect()
    out = []
    tables = [t for (t,) in con.execute("SHOW TABLES").fetchall()]
    for t in tables:
        cols = con.execute(f'DESCRIBE "{t}"').fetchall()
        n = con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
        coldesc = ", ".join(f"{c[0]} {c[1]}" for c in cols)
        out.append(f"{t} ({n} rows): {coldesc}")
    if own:
        con.close()
    return "\n".join(out)
