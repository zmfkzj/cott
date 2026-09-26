import contextlib
import io
from typing import cast

import click
from cott_runtime import CottList, Err, FrozenMap, I64, Nothing, Ok, Result, Some

from real.pgcli.cli_types import CliCommand, CliCommand_Launch, CliCommand_ShowHelp, CliError, CliError_Usage, CliOptions, PGCLI_HELP


def _flag(names: list[str], name: str, help_text: str) -> click.Option:
    return click.Option([*names, name], is_flag=True, default=False, help=help_text)


def _build_command(default_pgclirc: str) -> click.Command:
    params: list[click.Parameter] = [
        click.Option(["-h", "--host", "host"], default="", help="Host address of the postgres database."),
        click.Option(["-p", "--port", "port"], default=5432, type=click.INT, help="Port number at which the postgres instance is listening."),
        click.Option(["-U", "--username", "username_u"], help="Username to connect to the postgres database."),
        click.Option(["-u", "--user", "username_user"], help="Username to connect to the postgres database."),
        click.Option(["--timeout", "timeout"], type=click.INT, help="Seconds to wait for a connection before giving up (0 waits forever). Overrides the connection string and $PGCONNECT_TIMEOUT."),
        _flag(["-W", "--password"], "prompt_passwd", "Force password prompt."),
        _flag(["-w", "--no-password"], "never_prompt", "Never prompt for password."),
        _flag(["--single-connection"], "single_connection", "Do not use a separate connection for completions."),
        _flag(["-v", "--version"], "version", "Version of pgcli."),
        click.Option(["-d", "--dbname", "dbname_opt"], help="database name to connect to."),
        click.Option(["--pgclirc", "pgclirc"], default=default_pgclirc, type=click.Path(dir_okay=False), help="Location of pgclirc file."),
        click.Option(["-D", "--dsn", "dsn"], default="", help="Use DSN configured into the [alias_dsn] section of pgclirc file."),
        _flag(["--list-dsn"], "list_dsn", "list of DSN configured into the [alias_dsn] section of pgclirc file."),
        click.Option(["--row-limit", "row_limit"], type=click.INT, help="Set threshold for row limit prompt. Use 0 to disable prompt."),
        click.Option(["--application-name", "application_name"], default="pgcli", help="Application name for the connection."),
        _flag(["--less-chatty"], "less_chatty", "Skip intro on startup and goodbye on exit."),
        _flag(["-t", "--tuples-only"], "tuples_only", "Print rows only: no column headers, no status footer and no timing, like psql."),
        click.Option(["--prompt", "prompt"], help='Prompt format (Default: "\\u@\\h:\\d> ").'),
        click.Option(["--prompt-dsn", "prompt_dsn"], help='Prompt format for connections using DSN aliases (Default: "\\u@\\h:\\d> ").'),
        _flag(["-l", "--list"], "list_databases", "list available databases, then exit."),
        _flag(["--ping"], "ping", "Check database connectivity, then exit."),
        _flag(["--auto-vertical-output"], "auto_vertical_output", "Automatically switch to vertical output mode if the result is wider than the terminal width."),
        click.Option(["--warn", "warn"], help="Warn before running a destructive query."),
        click.Option(["--ssh-tunnel", "ssh_tunnel"], help="Open an SSH tunnel to the given address and connect to the database from it."),
        click.Option(["--log-file", "log_file"], help="Write all queries & output into a file, in addition to the normal output destination."),
        click.Option(["--init-command", "init_command"], help="SQL statement to execute after connecting."),
        click.Option(["-c", "--command", "commands"], multiple=True, help="run command (SQL or internal) and exit. Multiple -c options are allowed."),
        _flag(["-y", "--yes"], "force_destructive", "Force destructive commands without confirmation prompt."),
        click.Option(["-f", "--file", "input_files"], multiple=True, type=click.Path(exists=True, readable=True, dir_okay=False), help="execute commands from file, then exit. Multiple -f options are allowed."),
        click.Argument(["dbname"], default=None, nargs=1, required=False),
        click.Argument(["username"], default=None, nargs=1, required=False),
    ]
    return click.Command("pgcli", params=params)


def _opt_str(value: object) -> Some[str] | Nothing:
    if value is None:
        return Nothing()
    return Some(value=str(value))


def _opt_int(value: object) -> Some[I64] | Nothing:
    if isinstance(value, int) and not isinstance(value, bool):
        return Some(value=value)
    return Nothing()


def _str_list(value: object) -> CottList[str]:
    items: list[str] = []
    if isinstance(value, (tuple, list)):
        for item in tuple(cast(tuple[object, ...] | list[object], value)):
            items.append(str(item))
    return CottList(values=items)


def parse_pgcli_arguments(arguments: CottList[str], environment: FrozenMap[str, str], default_pgclirc: str) -> Result[CliCommand, CliError]:
    args: list[str] = [str(a) for a in arguments]
    default_map: dict[str, object] = {}
    env_names: list[tuple[str, str]] = [
        ("host", "PGHOST"),
        ("port", "PGPORT"),
        ("pgclirc", "PGCLIRC"),
        ("dsn", "DSN"),
        ("row_limit", "PGROWLIMIT"),
        ("application_name", "PGAPPNAME"),
        ("dbname", "PGDATABASE"),
        ("username", "PGUSER"),
    ]
    for param_name, env_name in env_names:
        if env_name in environment:
            default_map[param_name] = environment[env_name]
    command = _build_command(default_pgclirc)
    sink = io.StringIO()
    try:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            ctx = command.make_context("pgcli", args, default_map=default_map)
    except click.exceptions.Exit:
        return Ok(value=CliCommand_ShowHelp(text=PGCLI_HELP))
    except click.UsageError as error:
        out = io.StringIO()
        error.show(file=out)
        return Err(error=CliError_Usage(text=out.getvalue()))
    params = cast(dict[str, object], ctx.params)
    username_u = params.get("username_u")
    username_opt = username_u if username_u is not None else params.get("username_user")
    port = params.get("port")
    options = CliOptions(
        host=str(params.get("host")),
        port=port if isinstance(port, int) else 5432,
        username_option=_opt_str(username_opt),
        timeout=_opt_int(params.get("timeout")),
        force_password_prompt=bool(params.get("prompt_passwd")),
        never_password_prompt=bool(params.get("never_prompt")),
        single_connection=bool(params.get("single_connection")),
        version=bool(params.get("version")),
        dbname_option=_opt_str(params.get("dbname_opt")),
        pgclirc=str(params.get("pgclirc")),
        dsn=str(params.get("dsn")),
        list_dsn=bool(params.get("list_dsn")),
        row_limit=_opt_int(params.get("row_limit")),
        application_name=str(params.get("application_name")),
        less_chatty=bool(params.get("less_chatty")),
        tuples_only=bool(params.get("tuples_only")),
        prompt=_opt_str(params.get("prompt")),
        prompt_dsn=_opt_str(params.get("prompt_dsn")),
        list_databases=bool(params.get("list_databases")),
        ping=bool(params.get("ping")),
        auto_vertical_output=bool(params.get("auto_vertical_output")),
        warn=_opt_str(params.get("warn")),
        ssh_tunnel=_opt_str(params.get("ssh_tunnel")),
        log_file=_opt_str(params.get("log_file")),
        init_command=_opt_str(params.get("init_command")),
        commands=_str_list(params.get("commands")),
        force_destructive=bool(params.get("force_destructive")),
        files=_str_list(params.get("input_files")),
        dbname=_opt_str(params.get("dbname")),
        username=_opt_str(params.get("username")),
    )
    return Ok(value=CliCommand_Launch(options=options))
