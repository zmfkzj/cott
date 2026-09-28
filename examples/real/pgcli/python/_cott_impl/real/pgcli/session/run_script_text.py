from collections import deque

import sqlparse

from real.pgcli.session import watch_pgcli_command
from real.pgcli.session_types import ScriptOutcome, Session, TerminalSize


def _split_script(text: str) -> list[str]:
    pending: deque[str] = deque(sqlparse.split(text))
    statements: list[str] = []
    while pending:
        piece = pending.popleft().strip()
        if not piece:
            continue
        if piece.startswith("\\") and "\n" in piece:
            first, rest = piece.split("\n", 1)
            pending.extendleft(reversed(sqlparse.split(rest)))
            piece = first.strip()
        if piece:
            statements.append(piece)
    return statements


def run_script_text(session: Session, text: str, screen: TerminalSize) -> ScriptOutcome:
    current = session
    ok = True
    for statement in _split_script(text):
        outcome = watch_pgcli_command(current, statement, screen)
        current = outcome.session
        if not outcome.query.successful:
            ok = False
        if outcome.quit:
            return ScriptOutcome(session=current, ok=ok, quit=True)
        if not outcome.query.successful and current.settings.on_error != "RESUME":
            break
    return ScriptOutcome(session=current, ok=ok, quit=False)
