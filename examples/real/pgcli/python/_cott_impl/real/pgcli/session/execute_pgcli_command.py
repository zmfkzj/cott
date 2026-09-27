import dataclasses
import datetime
import re
from typing import Any, cast

import click
from cott_runtime import Err, Some

from real.pgcli.connection import executor_transaction_status, reconnect_executor
from real.pgcli.connection_types import ConnectError_Failed, ReconnectRequest, TransactionStatus_Active, TransactionStatus_InTransaction
from real.pgcli.output import timing_report
from real.pgcli.parseutils import is_destructive
from real.pgcli.session import confirm_destructive_query, evaluate_pgcli_command
from real.pgcli.session_types import CommandOutcome, EvaluateError_ConnectionLost, EvaluateError_Interrupted, EvaluateError_NotImplemented, Evaluation, QueryOutcome, RefreshKind_Nothing, Session, TerminalSize


def _empty_outcome(session: Session, text: str) -> CommandOutcome:
    query = QueryOutcome(
        query=text,
        successful=False,
        total_time=0.0,
        execution_time=0.0,
        meta_changed=False,
        db_changed=False,
        path_changed=False,
        mutated=False,
        is_special=False,
    )
    return CommandOutcome(session=session, query=query, refresh=RefreshKind_Nothing(), quit=False)


def _reconnect(session: Session) -> tuple[Session, str | None]:
    result = reconnect_executor(session.executor, ReconnectRequest(database="", user="", host="", port=""))
    if isinstance(result, Err):
        error = result.error
        if isinstance(error, ConnectError_Failed):
            return session, error.message
        return session, str(error)
    return dataclasses.replace(session, executor=result.value), None


def _cancelled(session: Session, text: str) -> CommandOutcome:
    if session.settings.destructive_warning_restarts_connection:
        session, _ = _reconnect(session)
        click.secho("cancelled query and restarted connection", err=True, fg="red")
    else:
        click.secho("cancelled query", err=True, fg="red")
    return _empty_outcome(session, text)


def _skip_file_routing(text: str) -> bool:
    return text.startswith(("\\o ", "\\log-file", "\\? ", "\\echo "))


def _hide_named_query(evaluation: Evaluation, text: str) -> bool:
    stripped = text.strip()
    return (
        evaluation.session.settings.hide_named_query_text
        and evaluation.query.successful
        and evaluation.query.is_special
        and stripped.startswith("\\n ")
        and not stripped.startswith("\\ns ")
        and not stripped.startswith("\\nd ")
    )


def _display_output(session: Session, output: str, screen: TerminalSize) -> None:
    special: Any = session.special.unwrap()
    pager = cast(object, special.pager_config)
    if not isinstance(pager, int):
        raise TypeError("pager_config must be an integer")
    if pager == 0 or session.settings.scripted:
        click.echo(output)
    elif pager == 1 and session.settings.table_format != "csv":
        lines = output.split("\n")
        if len(lines) >= screen.rows - 4 or any(
            len(re.sub(r"\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))", "", line)) > screen.columns
            for line in lines
        ):
            click.echo_via_pager(output)
        else:
            click.echo(output)
    elif pager == 1:
        click.echo(output)
    else:
        click.echo_via_pager(output)


def _route_output(evaluation: Evaluation, text: str, screen: TerminalSize) -> None:
    settings = evaluation.session.settings
    skip = _skip_file_routing(text)
    hide = _hide_named_query(evaluation, text)
    output_file = settings.output_file
    if isinstance(output_file, Some) and not skip:
        try:
            with open(output_file.value, "a", encoding="utf-8") as handle:
                if not hide:
                    click.echo(text, file=handle)
                click.echo(evaluation.output, file=handle)
                click.echo("", file=handle)
        except OSError as error:
            click.secho(str(error), err=True, fg="red")
    elif evaluation.items > 0:
        _display_output(evaluation.session, evaluation.output, screen)

    log_file = settings.log_file
    if isinstance(log_file, Some) and not skip and text.strip():
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
        _route_output(evaluation, text, screen)
    except KeyboardInterrupt:
        return


def _execute(session: Session, text: str, screen: TerminalSize, retry: bool) -> CommandOutcome:
    settings = session.settings
    try:
        if len(settings.destructive_warning) > 0:
            if settings.destructive_statements_require_transaction:
                status = executor_transaction_status(session.executor)
                if not isinstance(status, (TransactionStatus_Active, TransactionStatus_InTransaction)) and is_destructive(text, settings.destructive_warning):
                    click.secho("Destructive statements must be run within a transaction.")
                    return _cancelled(session, text)
            answer = confirm_destructive_query(text, settings.destructive_warning, settings.dsn_alias, settings.force_destructive)
            if isinstance(answer, Some):
                if not answer.value:
                    click.secho("Wise choice!")
                    return _cancelled(session, text)
                if not settings.force_destructive:
                    click.secho("Your call!")
        result = evaluate_pgcli_command(session, text, screen)
    except KeyboardInterrupt:
        return _cancelled(session, text)

    if isinstance(result, Err):
        error = result.error
        if isinstance(error, EvaluateError_Interrupted):
            return _cancelled(session, text)
        if isinstance(error, EvaluateError_NotImplemented):
            click.secho("Not Yet Implemented.", fg="yellow")
            return _empty_outcome(session, text)
        if isinstance(error, EvaluateError_ConnectionLost):
            click.secho(error.message, err=True, fg="red")
            if retry:
                return _empty_outcome(session, text)
            click.secho("Reconnecting...", fg="green")
            reconnected, failure = _reconnect(session)
            if failure is not None:
                click.secho("Reconnect Failed", fg="red")
                click.secho(failure, err=True, fg="red")
                return _empty_outcome(session, text)
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
            return _empty_outcome(reconnected, text)
        click.secho(error.message, err=True, fg="red")
        return _empty_outcome(session, text)

    evaluation = result.value
    if evaluation.quit:
        return CommandOutcome(session=evaluation.session, query=evaluation.query, refresh=evaluation.refresh, quit=True)
    _route_ignoring_interrupt(evaluation, text, screen)
    special: Any = evaluation.session.special.unwrap()
    timing = cast(object, special.timing_enabled)
    if isinstance(timing, bool) and timing:
        click.echo(timing_report(evaluation.query.total_time, evaluation.query.execution_time))
    return CommandOutcome(session=evaluation.session, query=evaluation.query, refresh=evaluation.refresh, quit=False)


def execute_pgcli_command(session: Session, text: str, screen: TerminalSize) -> CommandOutcome:
    return _execute(session, text, screen, False)
