import dataclasses
import time
from typing import Any, cast

import click
import pgspecial.iocommands

from real.pgcli.session import execute_pgcli_command
from real.pgcli.session_types import CommandOutcome, QueryOutcome, RefreshKind_Nothing, Session, TerminalSize


def _with_query(outcome: CommandOutcome, query: str, scripted: bool) -> CommandOutcome:
    settings = dataclasses.replace(outcome.session.settings, scripted=scripted)
    session = dataclasses.replace(outcome.session, settings=settings, last_query=query)
    return dataclasses.replace(outcome, session=session)


def _finish(last: CommandOutcome | None, current: Session, watch_sql: str, scripted: bool) -> CommandOutcome:
    if last is None:
        failed = QueryOutcome(query=watch_sql, successful=False, total_time=0.0, execution_time=0.0, meta_changed=False, db_changed=False, path_changed=False, mutated=False, is_special=False)
        return _with_query(CommandOutcome(session=current, query=failed, refresh=RefreshKind_Nothing(), quit=False), watch_sql, scripted)
    return _with_query(last, watch_sql, scripted)


def watch_pgcli_command(session: Session, text: str, screen: TerminalSize) -> CommandOutcome:
    iocommands: Any = pgspecial.iocommands
    parsed = cast(object, iocommands.get_watch_command(text))
    watch_sql: str | None = None
    seconds: float = 0.0
    seconds_text = "0"
    if isinstance(parsed, tuple):
        pair = cast(tuple[object, ...], parsed)
        first = pair[0] if len(pair) > 0 else None
        watch_sql = first if isinstance(first, str) else None
        second = pair[1] if len(pair) > 1 else 0
        if isinstance(second, (int, float)) and not isinstance(second, bool):
            seconds = float(second)
            seconds_text = str(second)
    if watch_sql is not None and not watch_sql.strip():
        if session.last_query:
            watch_sql = session.last_query
        else:
            click.secho("\\watch cannot be used with an empty query", err=True, fg="red")
            watch_sql = None
    original_scripted = session.settings.scripted
    if watch_sql is None:
        return _with_query(execute_pgcli_command(session, text, screen), text, original_scripted)
    current = dataclasses.replace(session, settings=dataclasses.replace(session.settings, scripted=True))
    last: CommandOutcome | None = None
    try:
        while True:
            last = execute_pgcli_command(current, watch_sql, screen)
            current = last.session
            click.echo("Waiting for " + seconds_text + " seconds before repeating")
            time.sleep(seconds)
    except KeyboardInterrupt:
        return _finish(last, current, watch_sql, original_scripted)
