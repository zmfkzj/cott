import dataclasses
import time
from typing import Any, cast

import click
import pgspecial.iocommands

from real.pgcli.session import execute_pgcli_command
from real.pgcli.session_types import CommandOutcome, QueryOutcome, RefreshKind_Nothing, Session, TerminalSize


def _finish_watch(last: CommandOutcome | None, current: Session, query: str, scripted: bool) -> CommandOutcome:
    if last is None:
        record = QueryOutcome(
            query=query,
            successful=False,
            total_time=0.0,
            execution_time=0.0,
            meta_changed=False,
            db_changed=False,
            path_changed=False,
            mutated=False,
            is_special=False,
        )
        last = CommandOutcome(session=current, query=record, refresh=RefreshKind_Nothing(), quit=False)
    settings = dataclasses.replace(last.session.settings, scripted=scripted)
    updated = dataclasses.replace(last.session, settings=settings, last_query=query)
    return dataclasses.replace(last, session=updated)


def watch_pgcli_command(session: Session, text: str, screen: TerminalSize) -> CommandOutcome:
    iocommands: Any = pgspecial.iocommands
    parsed = cast(object, iocommands.get_watch_command(text))
    if not isinstance(parsed, tuple):
        raise TypeError("Invalid \\watch command result")
    pair = cast(tuple[object, object], parsed)
    raw_query = pair[0]
    if raw_query is not None and not isinstance(raw_query, str):
        raise TypeError("Invalid \\watch query")
    watch_sql = raw_query
    if watch_sql is not None and not watch_sql.strip():
        if session.last_query:
            watch_sql = session.last_query
        else:
            click.secho("\\watch cannot be used with an empty query", err=True, fg="red")
            watch_sql = None
    if watch_sql is None:
        outcome = execute_pgcli_command(session, text, screen)
        updated = dataclasses.replace(outcome.session, last_query=text)
        return dataclasses.replace(outcome, session=updated)

    raw_seconds = pair[1]
    if isinstance(raw_seconds, bool) or not isinstance(raw_seconds, (int, float)):
        raise TypeError("Invalid \\watch interval")
    seconds = raw_seconds
    original_scripted = session.settings.scripted
    current = dataclasses.replace(session, settings=dataclasses.replace(session.settings, scripted=True))
    last: CommandOutcome | None = None
    try:
        while True:
            last = execute_pgcli_command(current, watch_sql, screen)
            current = last.session
            click.echo("Waiting for " + str(seconds) + " seconds before repeating")
            time.sleep(seconds)
    except KeyboardInterrupt:
        return _finish_watch(last, current, watch_sql, original_scripted)
