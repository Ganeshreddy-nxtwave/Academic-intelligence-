"""Turn a copilot answer (markdown) into a shareable, self-contained HTML doc.

Why HTML and not just the raw markdown: a generated HLID is full of tables, and raw
markdown shows those as pipe soup in Word/Docs. HTML renders them, opens in any
browser, and prints to PDF — the format a non-technical reader can actually use.
Self-contained (inline CSS, no assets) so it survives being emailed or dropped in Drive.
"""
import re

import markdown as _md

_CSS = """
body { font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
       max-width: 820px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; line-height: 1.55; }
h1, h2, h3 { line-height: 1.25; margin-top: 1.6em; }
h1 { border-bottom: 2px solid #eee; padding-bottom: .3em; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: .93em; }
th, td { border: 1px solid #d0d0d0; padding: 6px 10px; text-align: left; vertical-align: top; }
th { background: #f5f5f7; }
tr:nth-child(even) td { background: #fafafa; }
code { background: #f2f2f2; padding: 1px 5px; border-radius: 4px; font-size: .9em; }
pre { background: #f6f8fa; padding: 12px; border-radius: 6px; overflow-x: auto; }
blockquote { border-left: 3px solid #ccc; margin: 1em 0; padding: .2em 1em; color: #555; }
.meta { color: #888; font-size: .85em; margin-bottom: 2em; }
@media print { body { margin: 0; max-width: none; } }
"""


def slug(text, maxlen=50):
    """A safe, short filename stem from the question text."""
    s = re.sub(r"[^a-z0-9]+", "-", (text or "answer").lower()).strip("-")
    return (s[:maxlen] or "answer").rstrip("-")


def to_html(answer_md, question="", generated_at=""):
    """Render one answer to a standalone HTML document string."""
    body = _md.markdown(answer_md or "", extensions=["tables", "fenced_code", "sane_lists"])
    header = ""
    if question:
        header = f"<h1>{_escape(question)}</h1>"
    meta = f'<div class="meta">NIAT Learning Copilot{" · " + generated_at if generated_at else ""}</div>'
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{_escape(question) or 'NIAT Learning Copilot'}</title>"
        f"<style>{_CSS}</style></head><body>{header}{meta}{body}</body></html>"
    )


def _escape(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
