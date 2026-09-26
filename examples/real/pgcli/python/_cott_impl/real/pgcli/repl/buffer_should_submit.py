import sqlparse

from real.pgcli.parseutils import is_open_quote


def buffer_should_submit(text: str, multi_line: bool, multiline_mode: str) -> bool:
    if not multi_line:
        return True
    if multiline_mode == "safe":
        return False
    t = text.strip()
    if t.startswith("\\") or t.endswith("\\e") or t.endswith("\\G"):
        return True
    if t in ("exit", "quit", ":q", ""):
        return True
    return str(sqlparse.format(t, strip_comments=True)).strip().endswith(";") and not is_open_quote(t)
