import dataclasses
import logging
import os
import pathlib
import shutil
import sys
from typing import Any, Never, cast

import click
import configobj
import setproctitle
from cott_runtime import CottList, Err, FrozenMap, Nothing, Some
from real.pgcli.cli import obfuscate_process_title, parse_pgcli_arguments, session_settings_from
from real.pgcli.cli_types import CliCommand_ShowHelp, CliOptions, SetupEnvironment
from real.pgcli.completion import empty_completion_catalog, load_alias_map
from real.pgcli.completion_types import CompleterSettings, MetadataRefreshRequest
from real.pgcli.config import configure_pgcli_logging, load_pgcli_config, pgcli_config_directory
from real.pgcli.config_types import PgcliConfig
from real.pgcli.connection import apply_local_timezone, connection_spec_from_uri, lookup_pg_service, open_executor, select_connect_target
from real.pgcli.connection_types import ConnectError, ConnectError_AliasMissing, ConnectError_Failed, ConnectTarget_Alias, ConnectTarget_Conninfo, ConnectTarget_Service, ConnectTarget_Uri, ConnectionParam, ConnectionSpec, Executor, OpenRequest, TargetRequest
from real.pgcli.repl import run_pgcli_repl
from real.pgcli.repl_types import ReplSettings
from real.pgcli.session import create_special_handle, database_listing, ping_database, run_init_commands, run_script_text
from real.pgcli.session_types import EvaluateError, EvaluateError_ConnectionLost, EvaluateError_Interrupted, EvaluateError_NotImplemented, Session, SpecialSetup, TerminalSize


def _fail(message: str) -> Never:
    click.secho(message, fg="red", err=True)
    sys.exit(1)


def _connect_error_text(error: ConnectError) -> str:
    if isinstance(error, ConnectError_Failed):
        return error.message
    if isinstance(error, ConnectError_AliasMissing):
        return 'Could not find a DSN with alias ' + error.name + '. Please check the "[alias_dsn]" section in pgclirc.'
    return "service '" + error.service + "' was not found in " + error.file


def _evaluation_error_text(error: EvaluateError) -> str:
    if isinstance(error, EvaluateError_ConnectionLost):
        return error.message
    if isinstance(error, EvaluateError_Interrupted):
        return "Interrupted"
    if isinstance(error, EvaluateError_NotImplemented):
        return "Not Yet Implemented."
    return error.message


def _migrate_config(directory: str, home: str) -> None:
    location = directory.rstrip("/")
    if not os.path.exists(location):
        os.makedirs(location, exist_ok=True)
    old = os.path.join(home, ".pgclirc")
    if os.path.exists(old):
        path = directory + "config"
        if not os.path.exists(path):
            shutil.move(old, path)
            click.echo("Config file (~/.pgclirc) moved to new location " + path)
        else:
            click.echo("Config file is now located at " + path)
            click.echo("Please move the existing config file ~/.pgclirc to " + path)


def _print_dsn_list(pgclirc: str) -> Never:
    path = os.path.expanduser(pgclirc)
    if not os.path.exists(path):
        sys.exit(0)
    lines: list[str] = []
    try:
        config: Any = configobj.ConfigObj(path, interpolation=False, encoding="utf-8", file_error=True)
        raw = cast(object, config.get("alias_dsn"))
        if raw is not None:
            if not isinstance(raw, dict):
                raise ValueError("alias_dsn")
            for alias, dsn in cast(dict[object, object], raw).items():
                if not isinstance(dsn, str):
                    raise ValueError("alias_dsn")
                lines.append(str(alias) + " : " + dsn)
    except Exception:
        _fail('Invalid DSNs found in the config file. Please check the "[alias_dsn]" section in pgclirc.')
    for line in lines:
        click.echo(line)
    sys.exit(0)


def _configure_pager(config: PgcliConfig) -> None:
    logger = logging.getLogger("pgcli.main")
    pager = config.main.pager
    if pager:
        os.environ["PAGER"] = pager
        logger.info('Default pager found in config file: "%s"', pager)
    else:
        env_pager = os.environ.get("PAGER", "")
        if env_pager:
            logger.info('Default pager found in PAGER environment variable: "%s"', env_pager)
        else:
            logger.info("No default pager found in environment. Using os default pager")
    if not os.environ.get("LESS", ""):
        os.environ["LESS"] = "-SRXF"


def _open_selected_executor(options: CliOptions, config: PgcliConfig, home: str, environment: dict[str, str]) -> tuple[Executor, str | None]:
    pgservice = environment.get("PGSERVICE")
    selected = select_connect_target(TargetRequest(dbname_option=options.dbname_option, dbname_argument=options.dbname, username_option=options.username_option, username_argument=options.username, host=options.host, port=str(options.port), pgservice=Some(value=pgservice) if pgservice is not None else Nothing(), list_or_ping=options.list_databases or options.ping, dsn_alias=options.dsn, alias_dsn=config.alias_dsn))
    if isinstance(selected, Err):
        _fail(_connect_error_text(selected.error))
    target = selected.value
    alias: str | None = None
    extra: CottList[ConnectionParam] = CottList(values=[])
    spec: ConnectionSpec
    if isinstance(target, (ConnectTarget_Alias, ConnectTarget_Uri)):
        if isinstance(target, ConnectTarget_Alias):
            alias = target.name
        parsed = connection_spec_from_uri(target.uri)
        if isinstance(parsed, Err):
            _fail(_connect_error_text(parsed.error))
        spec = parsed.value
    elif isinstance(target, ConnectTarget_Conninfo):
        spec = ConnectionSpec(database="", host="", user=target.user, port="", password="", dsn=target.dsn, extra=extra)
    elif isinstance(target, ConnectTarget_Service):
        service_file = environment.get("PGSERVICEFILE", "")
        sysconfdir = environment.get("PGSYSCONFDIR", "")
        service = lookup_pg_service(target.service, service_file, sysconfdir, home)
        if isinstance(service, Err):
            _fail(_connect_error_text(service.error))
        found = service.value
        if not isinstance(found, Some):
            file = service_file or (sysconfdir + "/.pg_service.conf" if sysconfdir else home + "/.pg_service.conf")
            _fail("service '" + target.service + "' was not found in " + file)
        values = {parameter.name: parameter.value for parameter in found.value}
        spec = ConnectionSpec(database=values.get("dbname", ""), host=values.get("host", ""), user=target.user or values.get("user", ""), port=values.get("port", ""), password=values.get("password", ""), dsn="", extra=extra)
    else:
        spec = ConnectionSpec(database=target.database, host=target.host, user=target.user, port=target.port, password="", dsn="", extra=extra)
    opened = open_executor(OpenRequest(spec=spec, application_name=options.application_name, force_password_prompt=options.force_password_prompt, never_password_prompt=options.never_password_prompt, keyring_enabled=config.main.keyring, explicit_timeout=options.timeout, default_timeout=config.main.connect_timeout, pgpassword=environment.get("PGPASSWORD", ""), pgconnect_timeout=environment.get("PGCONNECT_TIMEOUT", ""), dsn_alias=Some(value=alias) if alias is not None else Nothing(), explicit_tunnel=options.ssh_tunnel, dsn_tunnels=config.dsn_ssh_tunnels, host_tunnels=config.ssh_tunnels))
    if isinstance(opened, Err):
        _fail(_connect_error_text(opened.error))
    return opened.value, alias


def _collect_init_commands(options: CliOptions, config: PgcliConfig, alias: str | None) -> list[str]:
    commands: list[str] = []
    for entry in config.init_commands:
        commands.extend(entry.commands)
    if alias is not None:
        for entry in config.alias_dsn_init_commands:
            if entry.name == alias:
                commands.extend(entry.commands)
                break
    init = options.init_command
    if isinstance(init, Some):
        commands.append(init.value)
    return commands


def _run_scripts(session: Session, options: CliOptions) -> Never:
    size = shutil.get_terminal_size()
    screen = TerminalSize(columns=size.columns, rows=size.lines)
    try:
        for command in options.commands:
            outcome = run_script_text(session, command, screen)
            session = outcome.session
            if outcome.quit:
                sys.exit(0)
            if not outcome.ok:
                break
    except Exception as error:
        _fail(str(error))
    if len(options.files) == 0:
        sys.exit(0)
    try:
        for name in options.files:
            with open(name, encoding="utf-8") as handle:
                content = handle.read()
            if content.strip():
                outcome = run_script_text(session, content, screen)
                session = outcome.session
                if outcome.quit:
                    sys.exit(0)
                if not outcome.ok:
                    break
    except Exception as error:
        _fail(str(error))
    sys.exit(0)


def _repl_settings(options: CliOptions, config: PgcliConfig, directory: str) -> ReplSettings:
    main = config.main
    history = directory + "history" if main.history_file == "default" else os.path.expanduser(main.history_file)
    alias_map: FrozenMap[str, str] = FrozenMap(values={})
    if main.alias_map_file:
        loaded = load_alias_map(pathlib.Path(main.alias_map_file))
        if isinstance(loaded, Err):
            _fail(loaded.error.message)
        alias_map = loaded.value
    if main.casing_file == "default":
        casing = Some(value=pathlib.Path(directory + "casing"))
    elif main.casing_file:
        casing = Some(value=pathlib.Path(os.path.expanduser(main.casing_file)))
    else:
        casing = Nothing()
    completer = CompleterSettings(keyword_casing=main.keyword_casing, qualify_columns=main.qualify_columns, asterisk_column_order=main.asterisk_column_order, search_path_filter=main.search_path_filter, generate_aliases=main.generate_aliases, alias_map=alias_map)
    return ReplSettings(syntax_style=main.syntax_style, colors=config.colors, show_bottom_toolbar=main.show_bottom_toolbar, wider_completion_menu=main.wider_completion_menu, min_num_menu_lines=main.min_num_menu_lines, multiline_continuation_char=main.multiline_continuation_char, auto_suggest=main.auto_suggest, history_file=history, single_connection=options.single_connection or main.always_use_single_connection, completer=completer, refresh=MetadataRefreshRequest(casing_file=casing, generate_casing_file=main.generate_casing_file))


def _run_body(arguments: CottList[str]) -> Never:
    environment = dict(os.environ)
    home = os.path.expanduser("~")
    xdg = environment.get("XDG_CONFIG_HOME")
    directory = pgcli_config_directory(Some(value=xdg) if xdg is not None else Nothing(), home)
    parsed = parse_pgcli_arguments(arguments, FrozenMap(values=environment), directory + "config")
    if isinstance(parsed, Err):
        click.echo(parsed.error.text, err=True, nl=False)
        sys.exit(2)
    command = parsed.value
    if isinstance(command, CliCommand_ShowHelp):
        click.echo(command.text, nl=False)
        sys.exit(0)
    options = command.options
    if options.version:
        click.echo("Version: 4.7.1")
        sys.exit(0)
    _migrate_config(directory, home)
    if options.list_dsn:
        _print_dsn_list(options.pgclirc)
    loaded = load_pgcli_config(pathlib.Path(options.pgclirc))
    if isinstance(loaded, Err):
        _fail(loaded.error.message)
    config = loaded.value
    configured = configure_pgcli_logging(config.main.log_file, config.main.log_level, directory)
    if isinstance(configured, Err):
        _fail(configured.error.message)
    _configure_pager(config)
    log_file = options.log_file
    if isinstance(log_file, Some):
        try:
            handle = open(log_file.value, "a+", encoding="utf-8")
            handle.close()
        except OSError as error:
            _fail(str(error))
    settings = session_settings_from(options, config, SetupEnvironment(home=home, colorterm=environment.get("COLORTERM", "")))
    special = create_special_handle(SpecialSetup(timing=config.main.timing and not options.tuples_only, enable_pager=config.main.enable_pager, config_path=pathlib.Path(options.pgclirc)))
    if isinstance(special, Err):
        _fail(_evaluation_error_text(special.error))
    executor, alias = _open_selected_executor(options, config, home, environment)
    if config.main.use_local_timezone:
        apply_local_timezone(executor)
    commands = _collect_init_commands(options, config, alias)
    if commands:
        click.echo("Running init commands: " + "; ".join(commands))
        initialized = run_init_commands(executor, CottList(values=commands))
        if isinstance(initialized, Err):
            _fail(_evaluation_error_text(initialized.error))
    if options.list_databases:
        listing = database_listing(executor)
        if isinstance(listing, Err):
            _fail(_evaluation_error_text(listing.error))
        click.echo(listing.value)
        sys.exit(0)
    if options.ping:
        if ping_database(executor):
            click.echo("PONG")
            sys.exit(0)
        _fail("Could not connect to the database. Please check that the database is running.")
    title = cast(object, setproctitle.getproctitle())
    setproctitle.setproctitle(obfuscate_process_title(title if isinstance(title, str) else str(title)))
    active_settings = dataclasses.replace(settings, dsn_alias=Some(value=alias) if alias is not None else Nothing())
    session = Session(settings=active_settings, executor=executor, special=special.value, catalog=empty_completion_catalog(), last_query="")
    if len(options.commands) != 0 or len(options.files) != 0:
        _run_scripts(session, options)
    run_pgcli_repl(session, _repl_settings(options, config, directory))
    sys.exit(0)


def run(arguments: CottList[str]) -> Never:
    try:
        _run_body(arguments)
    except KeyboardInterrupt:
        sys.exit(1)
