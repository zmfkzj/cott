import logging
from typing import cast

import click
import psycopg
import psycopg.sql
import tzlocal
from cott_runtime import UNIT, Unit

from real.pgcli.connection_types import Executor


def _echo_tz_error(message: str, server_tz: str) -> None:
    click.secho("Failed to determine the local time zone", err=True, fg="yellow")
    click.secho(message, err=True, fg="yellow")
    click.secho("Continuing with the default time zone as preset by the server (" + server_tz + ")", err=True, fg="yellow")
    click.secho("Set `use_local_timezone = False` in the config to avoid trying to override the server time zone\n", err=True, dim=True)


def apply_local_timezone(executor: Executor) -> Unit:
    conn = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
    try:
        with conn.cursor() as cur:
            cur.execute("show time zone")
            row = cur.fetchone()
        server_tz = "" if row is None else str(row[0])
        try:
            raw_tz = cast(object, tzlocal.get_localzone_name())
        except KeyError as error:
            _echo_tz_error(str(cast(tuple[object, ...], error.args)[0]), server_tz)
            return UNIT
        if not isinstance(raw_tz, str):
            _echo_tz_error("No local time zone configuration found\n", server_tz)
            return UNIT
        local_tz = raw_tz
        if local_tz != server_tz:
            click.secho("Using local time zone " + local_tz + " (server uses " + server_tz + ")", fg="green")
            click.secho("Use `set time zone <TZ>` to override, or set `use_local_timezone = False` in the config", dim=True)
            with conn.cursor() as cur:
                cur.execute(psycopg.sql.SQL("set time zone {}").format(psycopg.sql.Identifier(local_tz)))
    except psycopg.Error as error:
        logging.getLogger("pgcli.main").error("Error setting local time zone: %r", error)
    return UNIT
