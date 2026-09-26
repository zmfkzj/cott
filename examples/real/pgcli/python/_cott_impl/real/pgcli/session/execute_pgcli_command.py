import dataclasses
import datetime
import re
from typing import Any, Final, cast

import click
from cott_runtime import Err, Some

from real.pgcli.connection import executor_transaction_status, reconnect_executor
from real.pgcli.connection_types import ConnectError_AliasMissing, ConnectError_Failed, ReconnectRequest, TransactionStatus_Active, TransactionStatus_InTransaction
from real.pgcli.output import timing_report
from real.pgcli.parseutils import is_destructive
from real.pgcli.session import confirm_destructive_query, evaluate_pgcli_command
from real.pgcli.session_types import CommandOutcome, EvaluateError_ConnectionLost, EvaluateError_Interrupted, EvaluateError_NotImplemented, Evaluation, QueryOutcome, RefreshKind_Nothing, Session, TerminalSize

_ANSI: Final[str] = "\x1b(\\[.*?[@-~]|\\].*?(\x07|\x1b\\\\))"
_SKIP_PREFIXES: Final[str] = "\\o |\\log-file|\\? |\\echo "


def _empty_query(text: str) -> QueryOutcome:
    return QueryOutcome(query=text, successful=False, total_time=0.0, execution_time=0.0, meta_changed=False, db_changed=False, path_changed=False, mutated=False, is_special=False)


def _outcome(session: Session, text: str) -> CommandOutcome:
    return CommandOutcome(session=session, query=_empty_query(text), refresh=RefreshKind_Nothing(), quit=False)


def _reconnect(session: Session) -> Session | str:
    result = reconnect_executor(session.executor, ReconnectRequest(database="", user="", host="", port=""))
    if isinstance(result, Err):
        error = result.error
        if isinstance(error, ConnectError_Failed):
            return error.message
        if isinstance(error, ConnectError_AliasMissing):
            return error.name
        return error.service
    return dataclasses.replace(session, executor=result.value)


def _hide_text(evaluation: Evaluation, text: str) -> bool:
    stripped = text.strip()
    return evaluation.session.settings.hide_named_query_text and evaluation.query.successful and evaluation.query.is_special and stripped.startswith("\\n ") and not stripped.startswith("\\ns ") and not stripped.startswith("\\nd ")


def _show(session: Session, output: str, screen: TerminalSize) -> None:
    special: Any = session.special.unwrap()
    pager_raw = cast(object, special.pager_config)
    pager = int(pager_raw) if isinstance(pager_raw, int) else 0
    if pager == 0 or session.settings.scripted:
        click.echo(output)
    elif pager == 1 and session.settings.table_format != "csv":
        lines = output.split("\n")
        too_wide = any(len(re.sub(_ANSI, "", line)) > screen.columns for line in lines)
        if len(lines) >= screen.rows - 4 or too_wide:
            click.echo_via_pager(output)
        else:
            click.echo(output)
    elif pager == 1:
        click.echo(output)
    else:
        click.echo_via_pager(output)


def _route(evaluation: Evaluation, text: str, screen: TerminalSize) -> None:
    session = evaluation.session
    settings = session.settings
    skipped = text.startswith(tuple(_SKIP_PREFIXES.split("|")))
    hide = _hide_text(evaluation, text)
    output_file = settings.output_file
    if isinstance(output_file, Some) and not skipped:
        try:
            with open(output_file.value, "a", encoding="utf-8") as handle:
                if not hide:
                    click.echo(text, file=handle)
                click.echo(evaluation.output, file=handle)
                click.echo("", file=handle)
        except OSError as error:
            click.secho(str(error), err=True, fg="red")
    elif evaluation.items > 0:
        _show(session, evaluation.output, screen)
    log_file = settings.log_file
    if isinstance(log_file, Some) and not skipped and text.strip() != "":
        try:
            with open(log_file.value, "a", encoding="utf-8") as handle:
                click.echo(datetime.datetime.now().isoformat(), file=handle)
                if not hide:
                    click.echo(text, file=handle)
                click.echo(evaluation.output, file=handle)
                click.echo("", file=handle)
        except OSError as error:
            click.secho(str(error), err=True, fg="red")


def _route_ignoring_interrupt(evaluation: Evaluation, text: str, screen: TerminalSize) -> None:
    try:
        _route(evaluation, text, screen)
    except KeyboardInterrupt:
        return


def _cancelled(session: Session, text: str) -> CommandOutcome:
    if session.settings.destructive_warning_restarts_connection:
        reconnected = _reconnect(session)
        if isinstance(reconnected, Session):
            session = reconnected
        click.secho("cancelled query and restarted connection", err=True, fg="red")
    else:
        click.secho("cancelled query", err=True, fg="red")
    return _outcome(session, text)


def _execute(session: Session, text: str, screen: TerminalSize, retry: bool) -> CommandOutcome:
    settings = session.settings
    keywords = settings.destructive_warning
    if len(keywords) > 0:
        status = executor_transaction_status(session.executor)
        valid = isinstance(status, (TransactionStatus_Active, TransactionStatus_InTransaction))
        if settings.destructive_statements_require_transaction and not valid and is_destructive(text, keywords):
            click.secho("Destructive statements must be run within a transaction.")
            return _cancelled(session, text)
        answer = confirm_destructive_query(text, keywords, settings.dsn_alias, settings.force_destructive)
        if isinstance(answer, Some):
            if not answer.value:
                click.secho("Wise choice!")
                return _cancelled(session, text)
            if not settings.force_destructive:
                click.secho("Your call!")
    result = evaluate_pgcli_command(session, text, screen)
    if isinstance(result, Err):
        error = result.error
        if isinstance(error, EvaluateError_Interrupted):
            return _cancelled(session, text)
        if isinstance(error, EvaluateError_NotImplemented):
            click.secho("Not Yet Implemented.", fg="yellow")
            return _outcome(session, text)
        if isinstance(error, EvaluateError_ConnectionLost):
            click.secho(error.message, err=True, fg="red")
            if retry:
                return _outcome(session, text)
            click.secho("Reconnecting...", fg="green")
            reconnected = _reconnect(session)
            if not isinstance(reconnected, Session):
                click.secho("Reconnect Failed", fg="red")
                click.secho(reconnected, err=True, fg="red")
                return _outcome(session, text)
            click.secho("Reconnected!", fg="green")
            rerun = reconnected.settings.auto_retry_closed_connection
            if not rerun:
                try:
                    rerun = bool(click.confirm("Run the query from before reconnecting?"))
                except click.Abort:
                    rerun = False
            if rerun:
                click.secho("Running query...", fg="green")
                return _execute(reconnected, text, screen, True)
            return _outcome(reconnected, text)
        click.secho(error.message, err=True, fg="red")
        return _outcome(session, text)
    evaluation = result.value
    if evaluation.quit:
        return CommandOutcome(session=evaluation.session, query=evaluation.query, refresh=evaluation.refresh, quit=True)
    _route_ignoring_interrupt(evaluation, text, screen)
    special: Any = evaluation.session.special.unwrap()
    if bool(cast(object, special.timing_enabled)):
        click.echo(timing_report(evaluation.query.total_time, evaluation.query.execution_time))
    return CommandOutcome(session=evaluation.session, query=evaluation.query, refresh=evaluation.refresh, quit=False)


def execute_pgcli_command(session: Session, text: str, screen: TerminalSize) -> CommandOutcome:
    return _execute(session, text, screen, False)
