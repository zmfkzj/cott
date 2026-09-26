import dataclasses
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Never, cast

import pyarrow
import tomlkit
from cott_runtime import CottList, FrozenMap, Nothing, Ok, Opaque, Some

from real.harlequin.adapters import close_connection, connect
from real.harlequin.adapters_types import AdapterDescriptor, AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Chdb, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino, AdapterOption, AdapterSetting, ConnectionError_ReadOnlyUnsupported, ConnectionRequest, OptionKind, OptionKind_Choice, OptionKind_FilePath, OptionKind_Flag, OptionKind_Repeated, OptionKind_Text, SettingValue, SettingValue_Flag, SettingValue_Text, SettingValue_Values
from real.harlequin.cli import first_pass, harlequin_option_names
from real.harlequin.cli_types import HARLEQUIN_VERSION, SshSettings
from real.harlequin.config import config_search_paths, interpolate_profile, merge_config_files, read_config_file, select_profile, validate_config_file, write_profile
from real.harlequin.config_types import AdapterOptionSet, ConfigEntry, ConfigError, ConfigFile, ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Integer, ConfigValue_Real, ConfigValue_Text, MergedConfig, Profile
from real.harlequin.export import write_result
from real.harlequin.export_types import ExportOptionValue, ExportRequest
from real.harlequin.history import harlequin_paths, recent_queries
from real.harlequin.history_types import HistoryFilter, QueryStatus, QueryStatus_Error, QueryStatus_Ok
from real.harlequin.hsql import execute_hsql_request, hsql_error_line, hsql_exit_status, hsql_help, layout_text, parse_hsql_arguments, send_session_request, serve_hsql_session
from real.harlequin.hsql_types import HsqlArguments, HsqlContext, HsqlError_Connection, HsqlError_Crash, HsqlError_Interrupted, HsqlMode_ConfigMode, HsqlMode_Execute, HsqlMode_History, HsqlMode_HistorySearch, HsqlMode_Info, HsqlMode_Serve, HsqlMode_SessionReset, HsqlMode_SessionStatus, HsqlMode_Skill, HsqlMode_Spec, LayoutOptions, SqlSource_SqlFile
from real.harlequin.keymap import builtin_keymaps
from real.harlequin.results_types import ColumnInfo, ResultSet
from real.harlequin.sqltext import redact_connection_string, redact_text
from real.harlequin.sqltext_types import REDACTED
from real.harlequin.support import open_ssh_tunnel
from real.harlequin.support_types import SshTunnel


def _skill_text() -> str:
    lines = [
        "---",
        "name: hsql",
        "description: Run SQL against any database Harlequin can connect to, from the shell, and read the results as text, CSV, JSON or files.",
        "---",
        "",
        "# hsql: Harlequin's headless CLI",
        "",
        "`hsql` runs SQL and exits. It uses the same adapters, config files and profiles as `harlequin`.",
        "",
        "## Run SQL",
        "",
        "- `hsql -c \"select 1\"` runs against an in-memory DuckDB database.",
        "- `hsql my.db -c \"select * from t\"` opens a database file (DuckDB by default).",
        "- `hsql -a sqlite app.db -f query.sql` picks an adapter and reads SQL from a file (`-f -` reads stdin).",
        "- `hsql -P prod -c \"...\"` uses a profile from your Harlequin config.",
        "",
        "## Output",
        "",
        "- `--format table|markdown|vertical|csv|tsv|json|jsonl|parquet|orc|feather|arrow|none`",
        "  (shorthands `--csv`, `--json`, `--jsonl`, `--markdown`, `-x`).",
        "- `-o FILE` writes the output to a file; `-o DIR` writes one file per result.",
        "- `--limit N` caps fetched rows (default 500, `-1` for all); `--display-rows N` caps printed rows.",
        "- `-t` prints tuples only, `-A` unaligned, `--stats` adds a JSON summary on stderr.",
        "",
        "## Explore",
        "",
        "- `hsql --catalog --path 'main.*'` lists catalog entries; `--catalog-search TERM` searches them.",
        "- `hsql --history` and `--history-search TERM` show recently run queries.",
        "",
        "## Warm sessions",
        "",
        "- `hsql --serve NAME ...` keeps a connection open; `hsql --session NAME -c ...` (or `HSQL_SESSION=NAME`) sends queries to it.",
        "",
        "## Exit status",
        "",
        "0 ok, 1 query error, 2 usage or config error, 3 connection error, 4 timeout, 130 interrupted, 70 internal bug.",
    ]
    return "\n".join(lines) + "\n"


def _adapter_table() -> list[tuple[str, str, str, bool, bool, bool]]:
    return [
        ("duckdb", "DuckDB", "harlequin", True, True, True),
        ("sqlite", "SQLite", "harlequin", True, True, True),
        ("postgres", "Postgres", "harlequin-postgres", True, True, True),
        ("mysql", "MySQL", "harlequin-mysql", True, True, True),
        ("odbc", "ODBC", "harlequin-odbc", False, False, False),
        ("bigquery", "BigQuery", "harlequin-bigquery", False, False, False),
        ("trino", "Trino", "harlequin-trino", False, False, False),
        ("databricks", "Databricks", "harlequin-databricks", False, True, False),
        ("adbc", "ADBC", "harlequin-adbc", False, False, False),
        ("cassandra", "Cassandra", "harlequin-cassandra", False, False, False),
        ("nebulagraph", "NebulaGraph", "harlequin-nebulagraph", False, False, False),
        ("chdb", "chDB", "harlequin-chdb", True, True, True),
    ]


def _kind(name: str) -> AdapterKind:
    if name == "duckdb":
        return AdapterKind_DuckDb()
    if name == "sqlite":
        return AdapterKind_Sqlite()
    if name == "postgres":
        return AdapterKind_Postgres()
    if name == "mysql":
        return AdapterKind_MySql()
    if name == "odbc":
        return AdapterKind_Odbc()
    if name == "bigquery":
        return AdapterKind_BigQuery()
    if name == "trino":
        return AdapterKind_Trino()
    if name == "databricks":
        return AdapterKind_Databricks()
    if name == "adbc":
        return AdapterKind_Adbc()
    if name == "cassandra":
        return AdapterKind_Cassandra()
    if name == "nebulagraph":
        return AdapterKind_NebulaGraph()
    return AdapterKind_Chdb()


def _descriptors() -> list[AdapterDescriptor]:
    result: list[AdapterDescriptor] = []
    for name, display, dist, read_only, cancel, search in _adapter_table():
        result.append(AdapterDescriptor(kind=_kind(name), name=name, display_name=display, distribution=dist, details=f"The {display} adapter, from the {dist} distribution.", implements_read_only=read_only, implements_cancel=cancel, implements_catalog_search=search, implements_validate_sql=False))
    return result


def _option_specs(adapter: str) -> str:
    specs: dict[str, str] = {
        "duckdb": "init-path:p no-init:f extension:r force-install-extensions:f custom-extension-repo:t md_token!:t md_saas:f allow-unsigned-extensions:f",
        "sqlite": "init-path:p no-init:f extension:r lock-timeout:t detect-types:t isolation-level:c=DEFERRED|IMMEDIATE|EXCLUSIVE|NONE cached-statements:t mode:c=ro|rw|rwc|memory",
        "postgres": "host:t port:t dbname:t user:t password!:t passfile:p connect_timeout:t sslmode:c=disable|allow|prefer|require|verify-ca|verify-full sslcert:p sslkey:p sslrootcert:p application_name:t options:t",
        "mysql": "host:t port:t unix_socket:t database:t user:t password!:t password2!:t password3!:t connection-timeout:t ssl-ca:p ssl-cert:p ssl-key:p ssl-disabled:f openid-token-file:p enable-cleartext-plugin:f",
        "odbc": "",
        "bigquery": "project:t location:t",
        "trino": "host:t port:t user:t password!:t catalog:t schema:t require-auth:c=password|google sslcert:p",
        "databricks": "server-hostname:t http-path:t access-token!:t username:t password!:t auth-type:t client-id:t client-secret!:t init-path:p no-init:f skip-legacy-indexing:f",
        "adbc": "driver-type:c=flightsql|postgresql|snowflake|sqlite|duckdb driver-path:p db-kwargs-str!:t",
        "cassandra": "host:t port:t keyspace:t user:t password!:t protocol-version:t consistency-level:c=ANY|ONE|TWO|THREE|QUORUM|ALL|LOCAL_QUORUM|EACH_QUORUM|SERIAL|LOCAL_SERIAL|LOCAL_ONE",
        "nebulagraph": "host:t port:t user:t password!:t",
        "chdb": "uri:t path:p show-system:f catalog-search-limit:t",
    }
    return specs.get(adapter, "")


def _short_decls(adapter: str, name: str) -> list[str]:
    if adapter != "duckdb":
        return []
    shorts: dict[str, list[str]] = {"init-path": ["-i", "-init"], "extension": ["-e"]}
    return shorts.get(name, [])


def _adapter_options(adapter: str) -> list[AdapterOption]:
    options: list[AdapterOption] = []
    for spec in _option_specs(adapter).split():
        raw_name, _, code = spec.partition(":")
        secret = raw_name.endswith("!")
        name = raw_name.rstrip("!")
        kind: OptionKind
        if code == "f":
            kind = OptionKind_Flag()
        elif code == "r":
            kind = OptionKind_Repeated()
        elif code == "p":
            kind = OptionKind_FilePath()
        elif code.startswith("c="):
            kind = OptionKind_Choice(choices=CottList(values=code[2:].split("|")))
        else:
            kind = OptionKind_Text()
        label = name.replace("-", " ").replace("_", " ").title()
        options.append(AdapterOption(name=name, short_decls=CottList(values=_short_decls(adapter, name)), kind=kind, label=label, description=f"{label} for the {adapter} adapter.", default=Nothing(), secret=secret))
    return options


def _key(option: AdapterOption) -> str:
    return option.name.replace("-", "_")


def _kind_name(kind: OptionKind) -> str:
    if isinstance(kind, OptionKind_Flag):
        return "flag"
    if isinstance(kind, OptionKind_Repeated):
        return "repeated"
    if isinstance(kind, OptionKind_FilePath):
        return "path"
    if isinstance(kind, OptionKind_Choice):
        return "choice"
    return "text"


def _option_json(option: AdapterOption) -> dict[str, object]:
    obj: dict[str, object] = {"name": option.name, "flags": [f"--{option.name}", *[d for d in option.short_decls]], "profile_key": _key(option), "kind": _kind_name(option.kind), "label": option.label, "description": option.description, "default": option.default.value if isinstance(option.default, Some) else None, "secret": option.secret}
    kind = option.kind
    if isinstance(kind, OptionKind_Choice):
        obj["choices"] = [c for c in kind.choices]
    return obj


def _option_schema(option: AdapterOption) -> dict[str, object]:
    kind = option.kind
    if isinstance(kind, OptionKind_Flag):
        return {"type": "boolean", "description": option.description}
    if isinstance(kind, OptionKind_Repeated):
        return {"type": "array", "items": {"type": "string"}, "description": option.description}
    if isinstance(kind, OptionKind_Choice):
        return {"type": "string", "enum": [c for c in kind.choices], "description": option.description}
    return {"type": ["string", "number"], "description": option.description}


def _hsql_option_rows() -> list[tuple[str, str, str]]:
    return [
        ("-a, --adapter", "NAME", "The adapter to connect with (default duckdb)."),
        ("-c, --command", "TEXT", "SQL to run; repeatable, run in order."),
        ("-f, --file", "PATH", "A SQL file to run ('-' reads stdin); repeatable."),
        ("-o, --output", "PATH", "Write output to a file, or one file per result to a directory."),
        ("--format", "NAME", "table, markdown, vertical, csv, tsv, json, jsonl, ndjson, parquet, orc, feather, arrow or none (default table)."),
        ("--csv", "", "Shorthand for --format csv."),
        ("--json", "", "Shorthand for --format json."),
        ("--jsonl", "", "Shorthand for --format jsonl."),
        ("--markdown", "", "Shorthand for --format markdown."),
        ("-x, --vertical", "", "Shorthand for --format vertical."),
        ("-t, --tuples-only", "", "Print rows only, without header or footer."),
        ("-A, --no-align", "", "Unaligned text output."),
        ("--no-header", "", "Omit the header."),
        ("--no-footer", "", "Omit the row-count footer."),
        ("--null-string", "TEXT", "How SQL NULL is printed (default NULL)."),
        ("-P, --profile", "NAME", "A config profile to use ('None' for none)."),
        ("--config-path", "PATH", "A config file to read first."),
        ("-r, --read-only", "", "Open the connection read-only."),
        ("--timeout", "SECONDS", "Cancel the run after this many seconds."),
        ("--ssh-host", "TEXT", "Connect through an SSH tunnel to this host."),
        ("--ssh-forward", "TEXT", "An ssh -L forward; repeatable."),
        ("--ssh-batch-mode", "", "Never let ssh prompt."),
        ("--ssh-allow-reuse", "", "Reuse a listener already bound to a forwarded port."),
        ("--ssh-timeout", "SECONDS", "How long to wait for the tunnel."),
        ("--catalog", "", "List the data catalog."),
        ("--catalog-search", "TERM", "Search the data catalog."),
        ("--path", "TEXT", "The catalog level to list or search."),
        ("--history", "", "List recent queries."),
        ("--history-search", "TERM", "Search recent queries."),
        ("--config", "MODE", "show, list-profiles, validate, schema or init."),
        ("--spec", "", "Print hsql's options and adapters as JSON."),
        ("--info", "", "Print version, config and adapter information as JSON."),
        ("--skill", "", "Print the hsql skill document."),
        ("--limit", "N", "Rows to fetch per result (default 500; -1 for all)."),
        ("--display-rows", "N", "Rows to print per result (-1 for all)."),
        ("--result", "all|last|N", "Which results to write (default all)."),
        ("--on-error", "stop|continue", "Whether to keep running after a failed statement (default stop)."),
        ("--no-write-history", "", "Do not log queries to the shared history."),
        ("--stats", "", "Print a JSON summary to stderr."),
        ("--color", "auto|always|never", "Color text output (default never)."),
        ("--serve", "NAME", "Keep a warm session open under this name."),
        ("--session", "NAME", "Send the request to a warm session."),
        ("--session-reset", "", "Reconnect a warm session."),
        ("--session-status", "", "Describe a warm session."),
        ("--queue-timeout", "SECONDS", "How long a session request waits for its turn."),
        ("--idle-timeout", "SECONDS", "Stop a session after this idle time (default 1800)."),
        ("--max-lifetime", "SECONDS", "Stop a session after this age (default 28800)."),
        ("--help", "", "Show help and exit."),
        ("--version", "", "Show the version and exit."),
    ]


def _session_route(args: list[str], env: dict[str, str]) -> tuple[str, bool] | None:
    name: str | None = None
    serve = False
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--":
            break
        if arg == "--session" and i + 1 < len(args):
            name = args[i + 1]
            i += 2
            continue
        if arg.startswith("--session="):
            name = arg[len("--session="):]
        elif arg == "--serve" or arg.startswith("--serve="):
            serve = True
        i += 1
    if name is not None:
        return (name, False)
    if serve:
        return None
    from_env = env.get("HSQL_SESSION", "")
    if from_env != "":
        return (from_env, True)
    return None


def _wants_stdin(args: list[str]) -> bool:
    for i, arg in enumerate(args):
        if arg == "--":
            break
        if arg in ("--file=-", "-f-"):
            return True
        if arg in ("-f", "--file") and i + 1 < len(args) and args[i + 1] == "-":
            return True
    return False


def _config_failure(error: ConfigError) -> tuple[bytes, str, int]:
    return b"", f"hsql: error: {error.title}\n{error.message}\n", 2


def _usage(message: str) -> tuple[bytes, str, int]:
    return b"", f"hsql: error: {message}\n", 2


def _text_value(value: ConfigValue | None) -> str | None:
    if isinstance(value, ConfigValue_Text):
        return value.value
    if isinstance(value, (ConfigValue_Integer, ConfigValue_Real)):
        return str(value.value)
    return None


def _texts(value: ConfigValue | None) -> list[str]:
    if isinstance(value, ConfigValue_Array):
        return [item.value for item in value.values if isinstance(item, ConfigValue_Text)]
    if isinstance(value, ConfigValue_Text):
        return [value.value]
    return []


def _truthy(value: ConfigValue | None) -> bool:
    if isinstance(value, ConfigValue_Boolean):
        return value.value
    if isinstance(value, ConfigValue_Text):
        return value.value.lower() == "true"
    return False


def _setting(option: AdapterOption, value: ConfigValue) -> SettingValue | None:
    kind = option.kind
    if isinstance(kind, OptionKind_Flag):
        if isinstance(value, (ConfigValue_Boolean, ConfigValue_Text)):
            return SettingValue_Flag(value=_truthy(value))
        return None
    if isinstance(kind, OptionKind_Repeated):
        if isinstance(value, (ConfigValue_Array, ConfigValue_Text)):
            return SettingValue_Values(values=CottList(values=_texts(value)))
        return None
    text = _text_value(value)
    if text is None:
        return None
    return SettingValue_Text(value=text)


def _plain(value: ConfigValue) -> object:
    if isinstance(value, ConfigValue_Text):
        return value.value
    if isinstance(value, ConfigValue_Integer):
        return int(value.value)
    if isinstance(value, ConfigValue_Real):
        return float(value.value)
    if isinstance(value, ConfigValue_Boolean):
        return value.value
    if isinstance(value, ConfigValue_Array):
        return [_plain(item) for item in value.values]
    table: dict[str, object] = {}
    for entry in value.entries:
        table[entry.key] = _plain(entry.value)
    return table


def _masked(key: str, value: ConfigValue, secret_keys: set[str]) -> object:
    if key in secret_keys:
        return REDACTED
    if key == "conn_str":
        if isinstance(value, ConfigValue_Text):
            return redact_connection_string(value.value)
        if isinstance(value, ConfigValue_Array):
            return [redact_connection_string(item.value) if isinstance(item, ConfigValue_Text) else _plain(item) for item in value.values]
    return _plain(value)


def _guess_connection_id(adapter: str, conn: list[str], values: dict[str, ConfigValue]) -> str:
    if adapter in ("duckdb", "sqlite"):
        if not conn or conn == [""] or conn == [":memory:"]:
            return ""
        return ",".join(sorted(Path(p).resolve().as_posix() for p in conn))
    if adapter == "chdb":
        raw = conn[0] if conn else (_text_value(values.get("uri")) or _text_value(values.get("path")) or "")
        if raw in ("", ":memory:", "chdb://:memory:", "chdb::memory:"):
            return "chdb://"
        if "://" in raw or raw.startswith(("chdb:", "file:", "local:")):
            return raw
        return "file:" + Path(raw).resolve().as_posix()
    if len(conn) == 1:
        return conn[0]
    user = _text_value(values.get("user")) or _text_value(values.get("username")) or ""
    host = _text_value(values.get("host")) or _text_value(values.get("server_hostname")) or ""
    port = _text_value(values.get("port")) or ""
    database = _text_value(values.get("dbname")) or _text_value(values.get("database")) or _text_value(values.get("catalog")) or _text_value(values.get("keyspace")) or ""
    return f"{adapter}://{user}@{host}:{port}/{database}"


def _status_name(status: QueryStatus) -> str:
    if isinstance(status, QueryStatus_Ok):
        return "ok"
    if isinstance(status, QueryStatus_Error):
        return "error"
    return "canceled"


def _resolve(cwd: Path, text: str) -> Path:
    target = Path(text).expanduser()
    return target if target.is_absolute() else cwd / target


def _export_bytes(result_set: ResultSet, fmt: str, arguments: HsqlArguments) -> bytes | str:
    options: list[ExportOptionValue] = []
    if fmt in ("csv", "tsv"):
        null = arguments.null_string
        options.append(ExportOptionValue(name="na_rep", value=null.value if isinstance(null, Some) else ""))
        if arguments.tuples_only or arguments.no_header:
            options.append(ExportOptionValue(name="header", value="false"))
    if fmt == "json":
        options.append(ExportOptionValue(name="array", value="true"))
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / ("result." + fmt)
        written = write_result(result_set, ExportRequest(path=path, format=fmt, options=CottList(values=options)))
        if isinstance(written, Ok):
            try:
                return path.read_bytes()
            except OSError as error:
                return f"could not read the exported file: {error.strerror or error}"
        return f"could not write {fmt} output: {written.error}"


def _emit(result_set: ResultSet, arguments: HsqlArguments, cwd: Path, context: HsqlContext) -> tuple[bytes, str, int]:
    fmt = arguments.format
    notes = ""
    if result_set.truncated:
        notes += f"note: results truncated at --limit {arguments.limit}; pass --limit -1 for all rows\n"
    if fmt == "none":
        return b"", notes, 0
    output = arguments.output
    if fmt in ("table", "markdown", "md", "vertical"):
        display = arguments.display_rows
        max_rows: Some[int] | Nothing
        if isinstance(display, Some):
            max_rows = Nothing() if display.value < 0 else Some(value=display.value)
        else:
            max_rows = Some(value=10 if fmt == "vertical" else 40)
        color = arguments.color == "always" or (arguments.color == "auto" and context.stdout_tty and not context.no_color and not isinstance(output, Some))
        footer = not (arguments.tuples_only or arguments.no_footer)
        options = LayoutOptions(header=not (arguments.tuples_only or arguments.no_header), footer=footer, aligned=not arguments.no_align, null_string=arguments.null_string, color=color, max_rows=max_rows)
        data = layout_text(result_set, fmt, options).encode("utf-8")
        if not footer and isinstance(max_rows, Some) and result_set.fetched_row_count > max_rows.value:
            notes += f"note: printed {max_rows.value} of {result_set.fetched_row_count} rows; pass --display-rows -1 for all of them\n"
        suffix = ".md" if fmt in ("markdown", "md") else ".txt"
    else:
        if isinstance(arguments.display_rows, Some):
            notes += "note: --display-rows only applies to text layouts; use --limit to fetch fewer rows.\n"
        exported = _export_bytes(result_set, fmt, arguments)
        if isinstance(exported, str):
            return b"", notes + f"hsql: error: {exported}\n", 1
        data = exported
        suffix = "." + fmt
    if isinstance(output, Some):
        target = _resolve(cwd, output.value)
        if target.is_dir():
            target = target / f"result-1{suffix}"
            notes += f"note: wrote {target}\n"
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        except OSError as error:
            return b"", notes + f"hsql: error: could not write {target}: {error.strerror or error}\n", 2
        return b"", notes, 0
    return data, notes, 0


def _open_tunnel(values: dict[str, ConfigValue]) -> tuple[SshTunnel | None, str, str | None]:
    host = _text_value(values.get("ssh_host"))
    if host is None or host == "":
        return None, "", None
    timeout = 10.0
    raw_timeout = _text_value(values.get("ssh_timeout"))
    if raw_timeout is not None:
        try:
            timeout = float(raw_timeout)
        except ValueError:
            timeout = 10.0
    settings = SshSettings(host=host, forwards=CottList(values=_texts(values.get("ssh_forward"))), batch_mode=_truthy(values.get("ssh_batch_mode")), allow_reuse=_truthy(values.get("ssh_allow_reuse")), timeout_seconds=timeout)
    opened = open_ssh_tunnel(settings)
    if isinstance(opened, Ok):
        tunnel = opened.value
        return tunnel, "".join(f"note: {warning}\n" for warning in tunnel.warnings), None
    return None, "", opened.error.message


def _stop_tunnel(tunnel: SshTunnel | None) -> None:
    if tunnel is None:
        return
    handle = tunnel.process
    if handle.tag != "harlequin.ssh_process":
        return
    process = cast(subprocess.Popen[str], handle.unwrap())
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def _history(arguments: HsqlArguments, cwd: Path, context: HsqlContext, connection_filter: Some[str] | Nothing, term: str) -> tuple[bytes, str, int]:
    limit: Some[int] | Nothing = Nothing() if arguments.limit < 0 else Some(value=arguments.limit + 1)
    found = recent_queries(context.query_log, HistoryFilter(connection=connection_filter, search=term, program=Nothing(), status=Nothing()), limit)
    if not isinstance(found, Ok):
        return b"", f"hsql: error: could not read the query log at {found.error.path}: {found.error.message}\n", 1
    records = [record for record in found.value]
    truncated = arguments.limit >= 0 and len(records) > arguments.limit
    if truncated:
        records = records[: arguments.limit]
    pa: Any = pyarrow
    table = cast(object, pa.table({
        "run_at": pa.array([r.run_at for r in records], type=pa.string()),
        "program": pa.array([r.program for r in records], type=pa.string()),
        "profile": pa.array([r.profile.value if isinstance(r.profile, Some) else None for r in records], type=pa.string()),
        "adapter": pa.array([r.adapter for r in records], type=pa.string()),
        "status": pa.array([_status_name(r.status) for r in records], type=pa.string()),
        "rows": pa.array([r.rows.value if isinstance(r.rows, Some) else None for r in records], type=pa.int64()),
        "elapsed_ms": pa.array([r.elapsed_ms.value if isinstance(r.elapsed_ms, Some) else None for r in records], type=pa.float64()),
        "sql": pa.array([r.sql for r in records], type=pa.string()),
    }))
    labels = [("run_at", "s"), ("program", "s"), ("profile", "s"), ("adapter", "s"), ("status", "s"), ("rows", "##"), ("elapsed_ms", "#.#"), ("sql", "s")]
    count = len(records)
    result_set = ResultSet(statement="", columns=CottList(values=[ColumnInfo(name=n, type_label=t) for n, t in labels]), data=Opaque(tag="harlequin.arrow_table", value=table), row_count=count, fetched_row_count=count, truncated=truncated, elapsed_ms=0)
    return _emit(result_set, arguments, cwd, context)


def _config_mode(mode_name: str, arguments: HsqlArguments, merged: MergedConfig, files: list[ConfigFile], names: list[str], adapter_name: str, adapter_typed: bool, config_path: Path | None, cwd: Path) -> tuple[bytes, str, int]:
    if mode_name == "list-profiles":
        return "".join(f"{p.name}\n" for p in merged.profiles).encode("utf-8"), "", 0
    if mode_name == "show":
        secret_keys: set[str] = {"password"}
        for name in names:
            for option in _adapter_options(name):
                if option.secret:
                    secret_keys.add(_key(option))
        doc: dict[str, object] = {}
        default = merged.default_profile
        if isinstance(default, Some):
            doc["default_profile"] = default.value
        profiles: dict[str, object] = {}
        for profile in merged.profiles:
            body: dict[str, object] = {}
            for entry in profile.entries:
                body[entry.key] = _masked(entry.key, entry.value, secret_keys)
            profiles[profile.name] = body
        doc["profiles"] = profiles
        keymaps: dict[str, object] = {}
        for keymap in merged.keymaps:
            bindings: list[object] = []
            for binding in keymap.bindings:
                item: dict[str, object] = {"keys": binding.keys, "action": binding.action}
                if isinstance(binding.key_display, Some):
                    item["key_display"] = binding.key_display.value
                bindings.append(item)
            keymaps[keymap.name] = bindings
        if keymaps:
            doc["keymaps"] = keymaps
        if arguments.format == "json":
            return (json.dumps(doc, indent=2) + "\n").encode("utf-8"), "", 0
        tk: Any = tomlkit
        return str(cast(object, tk.dumps(doc))).encode("utf-8"), "", 0
    if mode_name == "validate":
        option_sets = CottList(values=[AdapterOptionSet(adapter=n, options=CottList(values=_adapter_options(n))) for n in names])
        keymap_names = CottList(values=[keymap.name for keymap in builtin_keymaps()])
        lines: list[str] = []
        for file in files:
            for problem in validate_config_file(file, option_sets, harlequin_option_names(), keymap_names):
                where = problem.key
                lines.append(f"{problem.path}: {where.value}: {problem.message}" if isinstance(where, Some) else f"{problem.path}: {problem.message}")
        if lines:
            return ("\n".join(lines) + "\n").encode("utf-8"), "", 2
        return b"config is valid\n", "", 0
    if mode_name == "schema":
        types: dict[str, object] = {
            "adapter": {"type": "string", "enum": names},
            "conn_str": {"type": "array", "items": {"type": "string"}},
            "keymap_name": {"type": "array", "items": {"type": "string"}},
            "ssh_forward": {"type": "array", "items": {"type": "string"}},
            "limit": {"type": "integer", "minimum": -1},
            "viewer_max_rows": {"type": "integer", "minimum": -1},
            "ssh_timeout": {"type": "number", "exclusiveMinimum": 0},
        }
        flags = ("no_download_tzdata", "no_write_history", "read_only", "ssh_allow_reuse", "ssh_batch_mode")
        properties: dict[str, object] = {}
        for key in harlequin_option_names():
            properties[key] = types.get(key, {"type": "boolean"} if key in flags else {"type": "string"})
        for name in names:
            for option in _adapter_options(name):
                properties.setdefault(_key(option), _option_schema(option))
        binding_schema: dict[str, object] = {"type": "object", "properties": {"keys": {"type": "string"}, "action": {"type": "string"}, "key_display": {"type": "string"}}, "required": ["keys", "action"], "additionalProperties": False}
        schema: dict[str, object] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Harlequin configuration",
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "default_profile": {"type": "string"},
                "profiles": {"type": "object", "additionalProperties": {"type": "object", "properties": properties}},
                "keymaps": {"type": "object", "additionalProperties": {"type": "array", "items": binding_schema}},
            },
        }
        return (json.dumps(schema, indent=2) + "\n").encode("utf-8"), "", 0
    if mode_name == "init":
        requested = arguments.profile
        if not isinstance(requested, Some):
            return _usage("--config init needs -P NAME to name the profile it writes.")
        if requested.value == "None":
            return _usage("'None' is not allowed as a profile name; pass another name with -P.")
        target = config_path if config_path is not None else cwd / "harlequin.toml"
        entries: list[ConfigEntry] = []
        if adapter_typed:
            entries.append(ConfigEntry(key="adapter", value=ConfigValue_Text(value=adapter_name)))
        if len(arguments.conn_str) > 0:
            entries.append(ConfigEntry(key="conn_str", value=ConfigValue_Array(values=CottList(values=[ConfigValue_Text(value=c) for c in arguments.conn_str]))))
        entries.extend(entry for entry in arguments.explicit)
        default_profile: Some[str] | Nothing = Nothing()
        existing = read_config_file(target)
        if isinstance(existing, Ok) and isinstance(existing.value, Some):
            default_profile = existing.value.value.default_profile
        written = write_profile(target, Profile(name=requested.value, entries=CottList(values=entries)), default_profile)
        if not isinstance(written, Ok):
            return _config_failure(written.error)
        return b"", f"note: wrote profile '{requested.value}' to {written.value}\n", 0
    return _usage(f"unknown --config mode {mode_name}")


def _cold(args: list[str], env: dict[str, str], environment: FrozenMap[str, str], descriptors: list[AdapterDescriptor], pre_stdin: str | None) -> tuple[bytes, str, int]:
    scanned = first_pass(CottList(values=args))
    home = Path.home()
    cwd = Path.cwd()
    paths = harlequin_paths(sys.platform, home, environment)
    config_path: Path | None = None
    if isinstance(scanned.config_path, Some):
        config_path = Path(scanned.config_path.value).expanduser()
    elif env.get("HARLEQUIN_CONFIG_PATH", "") != "":
        config_path = Path(env["HARLEQUIN_CONFIG_PATH"]).expanduser()
    explicit_path: Some[Path] | Nothing = Some(value=config_path) if config_path is not None else Nothing()
    files: list[ConfigFile] = []
    for path in config_search_paths(explicit_path, cwd, paths.config_dir, home):
        read = read_config_file(path)
        if not isinstance(read, Ok):
            return _config_failure(read.error)
        found = read.value
        if isinstance(found, Some):
            files.append(found.value)
    merged = merge_config_files(CottList(values=files))
    profile: Profile | None = None
    profile_error: ConfigError | None = None
    selected = select_profile(merged, scanned.profile)
    if isinstance(selected, Ok):
        chosen = selected.value
        if isinstance(chosen, Some):
            source: Some[str] | Nothing = Nothing()
            for item in merged.sources:
                if item.name == chosen.value.name:
                    source = Some(value=item.path)
            interpolated = interpolate_profile(chosen.value, environment, source)
            if isinstance(interpolated, Ok):
                profile = interpolated.value
            else:
                profile_error = interpolated.error
    else:
        profile_error = selected.error
    names = [d.name for d in descriptors]
    adapter_typed = isinstance(scanned.adapter, Some)
    adapter_name = "duckdb"
    if isinstance(scanned.adapter, Some):
        adapter_name = scanned.adapter.value
    elif profile is not None:
        for entry in profile.entries:
            value = entry.value
            if entry.key == "adapter" and isinstance(value, ConfigValue_Text):
                adapter_name = value.value.lower()
    known = adapter_name in names
    if not known and not adapter_typed:
        return _usage(f"Profile sets adapter to '{adapter_name}', which is not an installed adapter.")
    options = _adapter_options(adapter_name) if known else []
    parsed = parse_hsql_arguments(CottList(values=args), CottList(values=names), CottList(values=options))
    if not isinstance(parsed, Ok):
        return b"", hsql_error_line(parsed.error), hsql_exit_status(parsed.error)
    arguments = parsed.value
    if not known:
        return _usage(f"'{adapter_name}' is not an installed adapter.")
    descriptor = descriptors[names.index(adapter_name)]
    if arguments.show_help:
        return hsql_help(CottList(values=descriptors), Some(value=descriptor), CottList(values=options)).encode("utf-8"), "", 0
    if arguments.show_version:
        return f"hsql, version {HARLEQUIN_VERSION}\n".encode("utf-8"), "", 0
    mode = arguments.mode
    is_init = isinstance(mode, HsqlMode_ConfigMode) and mode.name == "init"
    if profile_error is not None and not is_init:
        return _config_failure(profile_error)
    values: dict[str, ConfigValue] = {}
    if profile is not None:
        for entry in profile.entries:
            if entry.key not in ("theme", "keymap_name", "show_files", "show_s3", "locale", "viewer_max_rows", "no_download_tzdata"):
                values[entry.key] = entry.value
    for entry in arguments.explicit:
        values[entry.key] = entry.value
    conn = [c for c in arguments.conn_str]
    if not conn:
        conn = _texts(values.get("conn_str"))
    read_only = arguments.read_only or _truthy(values.get("read_only"))
    limit_typed = any(a == "--limit" or a.startswith("--limit=") for a in args)
    limit_value = values.get("limit")
    if not limit_typed and isinstance(limit_value, ConfigValue_Integer) and limit_value.value >= -1:
        arguments = dataclasses.replace(arguments, limit=limit_value.value)
    if _truthy(values.get("no_write_history")):
        arguments = dataclasses.replace(arguments, write_history=False)
    settings: list[AdapterSetting] = []
    secrets: list[str] = []
    for option in options:
        key = _key(option)
        if key not in values:
            continue
        setting = _setting(option, values[key])
        if setting is None:
            continue
        settings.append(AdapterSetting(name=key, value=setting))
        if option.secret:
            text = _text_value(values[key])
            if text is not None and text != "":
                secrets.append(text)
    request = ConnectionRequest(adapter=_kind(adapter_name), conn_str=CottList(values=conn), read_only=read_only, settings=CottList(values=settings))
    context = HsqlContext(profile=Some(value=profile.name) if profile is not None else Nothing(), adapter_name=adapter_name, query_log=paths.query_log, stdout_tty=sys.stdout.isatty(), stderr_tty=sys.stderr.isatty(), no_color=env.get("NO_COLOR", "") != "", implements_cancel=descriptor.implements_cancel, implements_catalog_search=descriptor.implements_catalog_search, secrets=CottList(values=secrets))
    if isinstance(mode, HsqlMode_History) or isinstance(mode, HsqlMode_HistorySearch):
        narrow = isinstance(scanned.profile, Some) or adapter_typed or len(arguments.conn_str) > 0
        connection_filter: Some[str] | Nothing = Some(value=_guess_connection_id(adapter_name, conn, values)) if narrow else Nothing()
        term = mode.term if isinstance(mode, HsqlMode_HistorySearch) else ""
        return _history(arguments, cwd, context, connection_filter, term)
    if isinstance(mode, HsqlMode_ConfigMode):
        return _config_mode(mode.name, arguments, merged, files, names, adapter_name, adapter_typed, config_path, cwd)
    if isinstance(mode, HsqlMode_Spec):
        hsql_obj: dict[str, object] = {}
        for flags, metavar, help_text in _hsql_option_rows():
            hsql_obj[flags] = {"metavar": metavar, "help": help_text}
        adapters_obj: dict[str, object] = {}
        for name in names:
            if not adapter_typed or name == adapter_name:
                adapters_obj[name] = [_option_json(o) for o in _adapter_options(name)]
        return (json.dumps({"hsql": hsql_obj, "adapters": adapters_obj}, indent=2) + "\n").encode("utf-8"), "", 0
    if isinstance(mode, HsqlMode_Info):
        capabilities: dict[str, object] = {}
        for d in descriptors:
            capabilities[d.name] = {"display_name": d.display_name, "distribution": d.distribution, "read_only": d.implements_read_only, "cancel": d.implements_cancel, "catalog_search": d.implements_catalog_search, "validate_sql": d.implements_validate_sql}
        info: dict[str, object] = {"version": HARLEQUIN_VERSION, "python": sys.version.split()[0], "config_files": [f.path for f in files], "profile": profile.name if profile is not None else None, "adapters": capabilities}
        return (json.dumps(info, indent=2) + "\n").encode("utf-8"), "", 0
    if isinstance(mode, HsqlMode_Skill):
        output = arguments.output
        skill = _skill_text()
        if isinstance(output, Some):
            target = _resolve(cwd, output.value)
            if target.is_dir() or output.value.endswith(("/", os.sep)):
                target = target / "SKILL.md"
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(skill, encoding="utf-8")
            except OSError as error:
                return b"", f"hsql: error: could not write {target}: {error.strerror or error}\n", 2
            return b"", f"note: wrote {target}\n", 0
        return skill.encode("utf-8"), "", 0
    if isinstance(mode, HsqlMode_SessionReset) or isinstance(mode, HsqlMode_SessionStatus):
        return _usage("this option needs a running session: pass --session NAME or set HSQL_SESSION.")
    if isinstance(mode, HsqlMode_Execute) and len(arguments.sources) == 0:
        return _usage("no SQL to run. Pass -c/--command or -f/--file, or see 'hsql --help'.")
    tunnel, notes, tunnel_error = _open_tunnel(values)
    if tunnel_error is not None:
        return b"", redact_text(f"hsql: error: {tunnel_error}\n", context.secrets), 3
    try:
        if isinstance(mode, HsqlMode_Serve):
            status = serve_hsql_session(mode.name, request, context, arguments, environment)
            return b"", notes, status
        connected = connect(request)
        if not isinstance(connected, Ok):
            failure = connected.error
            if isinstance(failure, ConnectionError_ReadOnlyUnsupported):
                message = f"Harlequin could not connect read-only.\nThe {failure.adapter} adapter does not support read-only connections."
            else:
                message = f"{failure.title}\n{failure.message}"
            return b"", notes + redact_text(f"hsql: error: {message}\n", context.secrets), 3
        connection = connected.value
        stdin_text: Some[str] | Nothing = Nothing()
        if any(isinstance(s, SqlSource_SqlFile) and s.path == "-" for s in arguments.sources):
            stdin_text = Some(value=pre_stdin if pre_stdin is not None else sys.stdin.read())
        try:
            response = execute_hsql_request(connection, arguments, cwd, stdin_text, context)
        finally:
            close_connection(connection)
        return response.stdout, notes + response.stderr, response.status
    finally:
        _stop_tunnel(tunnel)


def _main(args: list[str]) -> tuple[bytes, str, int]:
    env = dict(os.environ)
    environment = FrozenMap(values=env)
    descriptors = _descriptors()
    if not args:
        return b"", hsql_help(CottList(values=descriptors), Nothing(), CottList(values=[])), 2
    route = _session_route(args, env)
    if route is None:
        return _cold(args, env, environment, descriptors, None)
    name, from_env = route
    pre_stdin = sys.stdin.read() if _wants_stdin(args) else None
    stdin_text: Some[str] | Nothing = Some(value=pre_stdin) if pre_stdin is not None else Nothing()
    sent = send_session_request(name, CottList(values=args), Path.cwd(), stdin_text, environment, sys.stdout.isatty(), sys.stderr.isatty())
    if isinstance(sent, Ok):
        return sent.value.stdout, sent.value.stderr, sent.value.status
    failure = sent.error
    if from_env and isinstance(failure, HsqlError_Connection) and failure.message.startswith("no session named"):
        stdout, stderr, status = _cold(args, env, environment, descriptors, pre_stdin)
        return stdout, f"note: HSQL_SESSION={name} is not running; running cold.\n" + stderr, status
    return b"", hsql_error_line(failure), hsql_exit_status(failure)


def run_hsql(arguments: CottList[str]) -> Never:
    args = [a for a in arguments]
    try:
        stdout, stderr, status = _main(args)
    except KeyboardInterrupt:
        stdout, stderr, status = b"", hsql_error_line(HsqlError_Interrupted()), 130
    except Exception as error:
        stdout, stderr, status = b"", hsql_error_line(HsqlError_Crash(message=str(error) or repr(error))), 70
    if stdout:
        sys.stdout.buffer.write(stdout)
    sys.stdout.flush()
    if stderr:
        sys.stderr.write(stderr)
        sys.stderr.flush()
    sys.exit(status)
