import sqlparse

from real.pgcli.session import watch_pgcli_command
from real.pgcli.session_types import ScriptOutcome, Session, TerminalSize


def _split_script(text: str) -> list[str]:
    pending = list(sqlparse.split(text))
    statements: list[str] = []
    while pending:
        piece = pending.pop(0).strip()
        if not piece:
            continue
        if piece.startswith("\\") and "\n" in piece:
            first, rest = piece.split("\n", 1)
            pending = list(sqlparse.split(rest)) + pending
            piece = first.strip()
            if not piece:
                continue
        statements.append(piece)
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
