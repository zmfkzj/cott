import sqlparse

from real.pgcli.session import watch_pgcli_command
from real.pgcli.session_types import ScriptOutcome, Session, TerminalSize


def _split_script(text: str) -> list[str]:
    pieces: list[str] = [str(p) for p in sqlparse.split(text)]
    statements: list[str] = []
    while pieces:
        stripped = pieces.pop(0).strip()
        if not stripped:
            continue
        if stripped.startswith("\\") and "\n" in stripped:
            first, rest = stripped.split("\n", 1)
            pieces = [str(p) for p in sqlparse.split(rest)] + pieces
            stripped = first.strip()
        statements.append(stripped)
    return statements


def run_script_text(session: Session, text: str, screen: TerminalSize) -> ScriptOutcome:
    current = session
    ok = True
    for statement in _split_script(text):
        outcome = watch_pgcli_command(current, statement, screen)
        current = outcome.session
        if outcome.quit:
            return ScriptOutcome(session=current, ok=ok, quit=True)
        if not outcome.query.successful:
            ok = False
            if current.settings.on_error != "RESUME":
                break
    return ScriptOutcome(session=current, ok=ok, quit=False)
