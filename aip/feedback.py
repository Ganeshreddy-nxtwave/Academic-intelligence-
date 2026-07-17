"""Append per-response feedback to a Google Sheet.

Write-only by design: nothing here re-enters the agent's prompt in v1. The row
captures everything a future learning loop would need (question, the exact SQL,
the answer, the verdict, and what the user wanted instead), so deferring the loop
costs time, not data.

Why a Sheet: Streamlit Community Cloud's filesystem is ephemeral — it wipes on
redeploy/sleep — so feedback written locally would silently vanish. A Sheet
survives restarts and is readable by the team without any tooling.
"""
import csv
import datetime as dt
import json
import os
import pathlib

HEADER = ["ts", "question", "sql", "answer", "verdict", "improvement", "model"]
LOCAL_FALLBACK = pathlib.Path("data/feedback_local.csv")
SHEET_NAME = "feedback_log"


def _client(sa_json):
    import gspread
    from google.oauth2.service_account import Credentials

    info = json.loads(sa_json) if isinstance(sa_json, str) else dict(sa_json)
    creds = Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds)


def log(question, sql, answer, verdict, improvement, model,
        sheet_id=None, sa_json=None):
    """Append one feedback row. Returns (ok, message).

    Never raises: a feedback-store outage must not take down Q&A. On failure we
    fall back to a local CSV and tell the caller it may not persist.
    """
    row = [
        dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        question or "",
        "\n---\n".join(sql or []),
        answer or "",
        verdict or "",
        improvement or "",
        model or "",
    ]
    sheet_id = sheet_id or os.environ.get("AIP_SHEET_ID")
    sa_json = sa_json or os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

    if sheet_id and sa_json:
        try:
            sh = _client(sa_json).open_by_key(sheet_id)
            try:
                ws = sh.worksheet(SHEET_NAME)
            except Exception:  # noqa: BLE001 - worksheet missing; create it
                ws = sh.add_worksheet(title=SHEET_NAME, rows=1000, cols=len(HEADER))
                ws.append_row(HEADER)
            ws.append_row(row, value_input_option="RAW")
            return True, "Saved."
        except Exception as e:  # noqa: BLE001 - degrade, never break chat
            _local(row)
            return False, f"Sheet unavailable ({type(e).__name__}); saved locally — may not persist."

    _local(row)
    return False, "No Sheet configured; saved locally — will NOT persist on Streamlit Cloud."


def _local(row):
    try:
        LOCAL_FALLBACK.parent.mkdir(parents=True, exist_ok=True)
        new = not LOCAL_FALLBACK.exists()
        with open(LOCAL_FALLBACK, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(HEADER)
            w.writerow(row)
    except OSError:
        pass  # nothing left to try; losing feedback must not break the answer
