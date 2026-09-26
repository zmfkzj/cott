from typing import Final, cast

import click

from real.pgcli.connection import executor_transaction_status
from real.pgcli.connection_types import TransactionStatus_Active, TransactionStatus_InTransaction
from real.pgcli.session import execute_pgcli_command
from real.pgcli.session_types import QuitDecision, Session, TerminalSize

_PROMPT: Final[str] = "A transaction is ongoing. Choose `c` to COMMIT, `r` to ROLLBACK, `a` to abort exit, `force` to exit anyway."


def confirm_quit_with_transaction(session: Session, screen: TerminalSize) -> QuitDecision:
    status = executor_transaction_status(session.executor)
    if not isinstance(status, (TransactionStatus_Active, TransactionStatus_InTransaction)):
        return QuitDecision(session=session, quit=True)
    while True:
        try:
            answer = str(cast(object, click.prompt(_PROMPT, default="a"))).lower()
        except click.Abort:
            click.echo()
            answer = "a"
        if answer == "a":
            return QuitDecision(session=session, quit=False)
        if answer == "force":
            return QuitDecision(session=session, quit=True)
        if answer == "c" or answer == "r":
            outcome = execute_pgcli_command(session, "commit" if answer == "c" else "rollback", screen)
            return QuitDecision(session=outcome.session, quit=outcome.query.successful)
