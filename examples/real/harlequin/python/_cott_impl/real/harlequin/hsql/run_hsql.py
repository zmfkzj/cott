import dataclasses
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path
from typing import Any, Final, Never, cast

import pyarrow
import tomlkit
from cott_runtime import CottList, FrozenMap, I64, Nothing, Ok, Opaque, Option, Some, U64
from real.harlequin.adapters import close_connection, connect
from real.harlequin.adapters_types import AdapterDescriptor, AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Chdb, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino, AdapterOption, AdapterSetting, ConnectionError_ReadOnlyUnsupported, ConnectionRequest, OptionKind, OptionKind_Choice, OptionKind_FilePath, OptionKind_Flag, OptionKind_Repeated, OptionKind_Text, SettingValue, SettingValue_Flag, SettingValue_Text, SettingValue_Values
from real.harlequin.cli import first_pass, harlequin_option_names
from real.harlequin.cli_types import HARLEQUIN_VERSION, SshSettings
from real.harlequin.config import config_search_paths, interpolate_profile, merge_config_files, read_config_file, select_profile, validate_config_file, write_profile
from real.harlequin.config_types import AdapterOptionSet, ConfigEntry, ConfigError, ConfigFile, ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Integer, ConfigValue_Real, ConfigValue_Text, MergedConfig, Profile
from real.harlequin.export import write_result
from real.harlequin.export_types import ExportError_InvalidOption, ExportError_PathIsDirectory, ExportError_WriteFailed, ExportOptionValue, ExportRequest
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

_SKILL: Final[str] = "---\nname: hsql\ndescription: Run SQL against a database and read the results without opening Harlequin's TUI.\n---\n\n# hsql: Harlequin's headless CLI\n\n`hsql` uses the same adapters, config files, and profiles as `harlequin`.\n\n## Run SQL\n\n- `hsql -c 'select 1'` uses an in-memory DuckDB database.\n- `hsql my.db -c 'select * from t'` opens a DuckDB file.\n- `hsql -a sqlite app.db -f query.sql` reads SQL from a file; `-f -` reads stdin.\n- `hsql -P prod -c 'select 1'` uses a saved profile.\n\n## Results\n\nUse `--format table|markdown|vertical|csv|tsv|json|jsonl|parquet|orc|feather|arrow|none`. `-o FILE` writes output; `-o DIR` writes one file per result. `--limit N` bounds fetched rows (default 500, -1 for unlimited); `--display-rows N` bounds text output. Use `--result last` or `--result N` for a single result set.\n\n## Explore and reuse\n\n`--catalog` and `--catalog-search TERM` inspect the catalog; `--path` selects a level. `--history` and `--history-search TERM` read query history. `--serve NAME` keeps a connection open; `--session NAME -c 'select 1'` or `HSQL_SESSION=NAME` sends it queries.\n\nExit statuses: 0 success, 1 query failure, 2 usage/config error, 3 connection failure, 4 timeout, 130 interruption, 70 internal error.\n"


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
    return [AdapterDescriptor(kind=_kind(name), name=name, display_name=display, distribution=distribution, details=f"The {display} adapter, from the {distribution} distribution.", implements_read_only=read_only, implements_cancel=cancel, implements_catalog_search=search, implements_validate_sql=False) for name, display, distribution, read_only, cancel, search in _adapter_table()]


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
    return specs[adapter]


def _adapter_options(adapter: str) -> list[AdapterOption]:
    defaults: dict[str, str] = {
        "duckdb.init-path": "~/.duckdbrc", "sqlite.init-path": "~/.sqliterc",
        "sqlite.lock-timeout": "5.0", "sqlite.cached-statements": "128", "sqlite.isolation-level": "DEFERRED",
        "databricks.init-path": "~/.databricksrc", "cassandra.consistency-level": "LOCAL_ONE",
        "chdb.catalog-search-limit": "100",
    }
    options: list[AdapterOption] = []
    for spec in _option_specs(adapter).split():
        raw, _, code = spec.partition(":")
        secret = raw.endswith("!")
        name = raw.removesuffix("!")
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
        short: list[str] = []
        if adapter == "duckdb" and name == "init-path":
            short = ["-i", "-init"]
        elif adapter == "duckdb" and name == "extension":
            short = ["-e"]
        default = defaults.get(f"{adapter}.{name}")
        label = name.replace("-", " ").replace("_", " ").title()
        options.append(AdapterOption(name=name, short_decls=CottList(values=short), kind=kind, label=label, description=f"{label} for the {adapter} adapter.", default=Some(value=default) if default is not None else Nothing(), secret=secret))
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
    row: dict[str, object] = {"name": option.name, "flags": [f"--{option.name}", *option.short_decls], "profile_key": _key(option), "kind": _kind_name(option.kind), "label": option.label, "description": option.description, "default": option.default.value if isinstance(option.default, Some) else None, "secret": option.secret}
    if isinstance(option.kind, OptionKind_Choice):
        row["choices"] = list(option.kind.choices)
    return row


def _option_schema(option: AdapterOption) -> dict[str, object]:
    kind = option.kind
    if isinstance(kind, OptionKind_Flag):
        return {"type": "boolean", "description": option.description}
    if isinstance(kind, OptionKind_Repeated):
        return {"type": "array", "items": {"type": "string"}, "description": option.description}
    if isinstance(kind, OptionKind_Choice):
        return {"type": "string", "enum": list(kind.choices), "description": option.description}
    return {"type": ["string", "number"], "description": option.description}


def _session_route(args: list[str], environment: dict[str, str]) -> tuple[str, bool] | None:
    session: str | None = None
    serves = False
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            break
        if arg == "--session" and index + 1 < len(args):
            session = args[index + 1]
            index += 2
            continue
        if arg.startswith("--session="):
            session = arg[len("--session="):]
        if arg == "--serve" or arg.startswith("--serve="):
            serves = True
        index += 1
    if session is not None:
        return session, False
    if serves:
        return None
    name = environment.get("HSQL_SESSION", "")
    return (name, True) if name else None


def _wants_stdin(args: list[str]) -> bool:
    for index, arg in enumerate(args):
        if arg == "--":
            break
        if arg in ("--file=-", "-f-"):
            return True
        if arg in ("-f", "--file") and index + 1 < len(args) and args[index + 1] == "-":
            return True
    return False


def _typed(args: list[str], long_name: str, short_name: str) -> bool:
    for arg in args:
        if arg == "--":
            break
        if arg == long_name or arg.startswith(long_name + "="):
            return True
        if short_name and arg.startswith(short_name) and not arg.startswith("--"):
            return True
    return False


def _config_failure(error: ConfigError) -> tuple[bytes, str, I64]:
    return b"", f"hsql: error: {error.title}\n{error.message}\n", 2


def _usage(message: str) -> tuple[bytes, str, I64]:
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
        return value.value.casefold() == "true"
    return False


def _setting(option: AdapterOption, value: ConfigValue) -> SettingValue | None:
    kind = option.kind
    if isinstance(kind, OptionKind_Flag):
        if isinstance(value, (ConfigValue_Boolean, ConfigValue_Text)):
            return SettingValue_Flag(value=_truthy(value))
        return None
    if isinstance(kind, OptionKind_Repeated):
        if isinstance(value, ConfigValue_Array):
            return SettingValue_Values(values=CottList(values=_texts(value)))
        return None
    if isinstance(kind, OptionKind_Choice):
        text = _text_value(value)
        if text is not None:
            for choice in kind.choices:
                if choice.casefold() == text.casefold():
                    return SettingValue_Text(value=choice)
        return None
    text = _text_value(value)
    return SettingValue_Text(value=text) if text is not None else None


def _plain(value: ConfigValue) -> object:
    if isinstance(value, ConfigValue_Text):
        return value.value
    if isinstance(value, ConfigValue_Integer):
        return value.value
    if isinstance(value, ConfigValue_Real):
        return value.value
    if isinstance(value, ConfigValue_Boolean):
        return value.value
    if isinstance(value, ConfigValue_Array):
        return [_plain(item) for item in value.values]
    entries: dict[str, object] = {}
    for entry in value.entries:
        entries[entry.key] = _plain(entry.value)
    return entries


def _masked(key: str, value: ConfigValue, secret_keys: set[str]) -> object:
    if key in secret_keys:
        return REDACTED
    if key == "conn_str":
        if isinstance(value, ConfigValue_Text):
            return redact_connection_string(value.value)
        if isinstance(value, ConfigValue_Array):
            return [redact_connection_string(item.value) if isinstance(item, ConfigValue_Text) else _plain(item) for item in value.values]
    return _plain(value)


def _connection_secrets(conn: list[str]) -> list[str]:
    secrets: list[str] = []
    for text in conn:
        for match in re.finditer(r"://[^/?#@\s]*?:([^/?#@\s]+)@", text):
            secrets.append(match.group(1))
        for match in re.finditer(r"[\w.\-]*(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)[\w.\-]*\s*=\s*(?:'([^']*)'|\"([^\"]*)\"|([^&;\s]+))", text, re.IGNORECASE):
            for group in (1, 2, 3):
                secret = match.group(group)
                if secret is not None:
                    secrets.append(secret)
                    break
    return secrets


def _guess_connection_id(adapter: str, conn: list[str], values: dict[str, ConfigValue]) -> str:
    if adapter in ("duckdb", "sqlite"):
        mode = _text_value(values.get("mode"))
        if not conn or conn == [""] or conn == [":memory:"] or (adapter == "sqlite" and mode is not None and mode.casefold() == "memory"):
            return ""
        paths: list[str] = []
        for text in conn:
            if text.startswith("file::memory:"):
                return ""
            if text.startswith("file:"):
                parsed = urllib.parse.urlsplit(text)
                paths.append(Path(urllib.parse.unquote(parsed.path)).resolve().as_posix())
            else:
                paths.append(Path(text).resolve().as_posix())
        return ",".join(sorted(paths))
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
    database = _text_value(values.get("dbname")) or _text_value(values.get("database")) or _text_value(values.get("catalog")) or _text_value(values.get("keyspace")) or _text_value(values.get("project")) or _text_value(values.get("http_path")) or ""
    return f"{adapter}://" + (f"{user}@" if user else "") + host + (f":{port}" if port else "") + (f"/{database}" if database else "")


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
                return f"could not read the exported file: {error}"
        failure = written.error
        if isinstance(failure, ExportError_WriteFailed):
            return f"{failure.title}\n{failure.message}"
        if isinstance(failure, ExportError_InvalidOption):
            return f"Invalid {failure.name}: {failure.message}"
        if isinstance(failure, ExportError_PathIsDirectory):
            return f"{failure.path} is a directory"
        return f"Unknown output format: {failure.name}"


def _emit(result_set: ResultSet, arguments: HsqlArguments, cwd: Path, context: HsqlContext) -> tuple[bytes, str, I64]:
    fmt = arguments.format
    notes = ""
    if result_set.truncated:
        notes += f"note: results truncated at --limit {arguments.limit}; pass --limit -1 for all rows\n"
    if fmt == "none":
        if isinstance(arguments.display_rows, Some):
            notes += "note: --display-rows only applies to text layouts; use --limit to fetch fewer rows.\n"
        return b"", notes, 0
    output = arguments.output
    if fmt in ("table", "markdown", "md", "vertical"):
        display = arguments.display_rows
        max_rows: Option[U64]
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
        directory = target.is_dir() or output.value.endswith(("/", os.sep))
        if directory:
            target = target / f"result-1{suffix}"
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        except OSError as error:
            return b"", notes + f"hsql: error: could not write {target}: {error}\n", 2
        if directory:
            notes += f"note: wrote {target}\n"
        return b"", notes, 0
    return data, notes, 0


def _history(arguments: HsqlArguments, cwd: Path, context: HsqlContext, connection_filter: Option[str], term: str) -> tuple[bytes, str, I64]:
    limit: Option[U64] = Nothing() if arguments.limit < 0 else Some(value=arguments.limit + 1)
    found = recent_queries(context.query_log, HistoryFilter(connection=connection_filter, search=term, program=Nothing(), status=Nothing()), limit)
    if not isinstance(found, Ok):
        return b"", f"hsql: error: could not read the query log at {found.error.path}: {found.error.message}\n", 1
    records = list(found.value)
    truncated = arguments.limit >= 0 and len(records) > arguments.limit
    if truncated:
        records = records[:arguments.limit]
    pa: Any = pyarrow
    raw_table: object = cast(object, pa.table({
        "run_at": pa.array([record.run_at for record in records], type=pa.string()),
        "program": pa.array([record.program for record in records], type=pa.string()),
        "profile": pa.array([record.profile.value if isinstance(record.profile, Some) else None for record in records], type=pa.string()),
        "adapter": pa.array([record.adapter for record in records], type=pa.string()),
        "status": pa.array([_status_name(record.status) for record in records], type=pa.string()),
        "rows": pa.array([record.rows.value if isinstance(record.rows, Some) else None for record in records], type=pa.int64()),
        "elapsed_ms": pa.array([record.elapsed_ms.value if isinstance(record.elapsed_ms, Some) else None for record in records], type=pa.float64()),
        "sql": pa.array([record.sql for record in records], type=pa.string()),
    }))
    if not isinstance(raw_table, pa.Table):
        raise TypeError("pyarrow did not return a Table")
    labels = [("run_at", "s"), ("program", "s"), ("profile", "s"), ("adapter", "s"), ("status", "s"), ("rows", "##"), ("elapsed_ms", "#.#"), ("sql", "s")]
    count = len(records)
    result_set = ResultSet(statement="", columns=CottList(values=[ColumnInfo(name=name, type_label=label) for name, label in labels]), data=Opaque(tag="harlequin.arrow_table", value=raw_table), row_count=count, fetched_row_count=count, truncated=truncated, elapsed_ms=0)
    return _emit(result_set, arguments, cwd, context)


def _hsql_option_rows() -> list[tuple[str, str, str]]:
    return [
        ("-a, --adapter", "NAME", "The database adapter to use (default duckdb)."),
        ("-c, --command", "TEXT", "Run this SQL; repeatable, in source order."),
        ("-f, --file", "PATH", "Run SQL from this file; - reads stdin."),
        ("-o, --output", "PATH", "Write results to a file or one per result to a directory."),
        ("--format", "NAME", "table, markdown, md, vertical, csv, tsv, json, jsonl, ndjson, parquet, orc, feather, arrow or none (default table)."),
        ("--csv", "", "Shorthand for --format csv."),
        ("--json", "", "Shorthand for --format json."),
        ("--jsonl", "", "Shorthand for --format jsonl."),
        ("--markdown", "", "Shorthand for --format markdown."),
        ("-x, --vertical", "", "Shorthand for --format vertical."),
        ("-t, --tuples-only", "", "Omit headers and footers."),
        ("-A, --no-align", "", "Unaligned text output."),
        ("--no-header", "", "Omit the header."),
        ("--no-footer", "", "Omit the row-count footer."),
        ("--null-string", "TEXT", "Text to print for SQL NULL."),
        ("-P, --profile", "NAME", "Use a config profile; None disables profiles."),
        ("--config-path", "PATH", "Read this config file first."),
        ("-r, --read-only", "", "Open read-only."),
        ("--timeout", "SECONDS", "Cancel a query after this many seconds."),
        ("--ssh-host", "TEXT", "Open an SSH tunnel to this host."),
        ("--ssh-forward", "TEXT", "An SSH port forward; repeatable."),
        ("--ssh-batch-mode", "", "Never prompt for SSH credentials."),
        ("--ssh-allow-reuse", "", "Reuse an existing forwarded-port listener."),
        ("--ssh-timeout", "SECONDS", "Seconds to wait for the tunnel."),
        ("--catalog", "", "Print the database catalog."),
        ("--catalog-search", "TERM", "Search the catalog."),
        ("--path", "TEXT", "Select the catalog level."),
        ("--history", "", "Print recent queries."),
        ("--history-search", "TERM", "Search recent queries."),
        ("--config", "MODE", "show, list-profiles, validate, schema or init."),
        ("--spec", "", "Print the CLI specification as JSON."),
        ("--info", "", "Print version, config and adapter information as JSON."),
        ("--skill", "", "Print the hsql skill document."),
        ("--limit", "N", "Rows fetched per result (default 500; -1 for unlimited)."),
        ("--display-rows", "N", "Rows printed per result (-1 for unlimited)."),
        ("--result", "all|last|N", "Choose results (default all)."),
        ("--on-error", "stop|continue", "Stop or continue after a statement fails."),
        ("--no-write-history", "", "Do not log queries."),
        ("--stats", "", "Print JSON timing and result statistics."),
        ("--color", "auto|always|never", "When to color text (default never)."),
        ("--serve", "NAME", "Serve a persistent session."),
        ("--session", "NAME", "Send a request to a session."),
        ("--session-reset", "", "Reconnect a session."),
        ("--session-status", "", "Describe a session."),
        ("--queue-timeout", "SECONDS", "Maximum time to wait behind another request."),
        ("--idle-timeout", "SECONDS", "Stop a served session after idle seconds (default 1800)."),
        ("--max-lifetime", "SECONDS", "Stop a served session after this age (default 28800)."),
        ("--help", "", "Show help and exit."),
        ("--version", "", "Show the version and exit."),
    ]


def _config_mode(mode_name: str, arguments: HsqlArguments, raw_args: list[str], merged: MergedConfig, files: list[ConfigFile], names: list[str], adapter_name: str, adapter_typed: bool, config_path: Path | None, cwd: Path) -> tuple[bytes, str, I64]:
    if mode_name == "list-profiles":
        return "".join(f"{profile.name}\n" for profile in merged.profiles).encode("utf-8"), "", 0
    if mode_name == "show":
        secret_keys: set[str] = set()
        for name in names:
            for option in _adapter_options(name):
                if option.secret:
                    secret_keys.add(_key(option))
        document: dict[str, object] = {}
        if isinstance(merged.default_profile, Some):
            document["default_profile"] = merged.default_profile.value
        document["profiles"] = {profile.name: {entry.key: _masked(entry.key, entry.value, secret_keys) for entry in profile.entries} for profile in merged.profiles}
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
            document["keymaps"] = keymaps
        if arguments.format == "json":
            return (json.dumps(document, indent=2) + "\n").encode("utf-8"), "", 0
        tk: Any = tomlkit
        rendered: object = cast(object, tk.dumps(document))
        if not isinstance(rendered, str):
            raise TypeError("tomlkit did not render TOML")
        return rendered.encode("utf-8"), "", 0
    if mode_name == "validate":
        option_sets = CottList(values=[AdapterOptionSet(adapter=name, options=CottList(values=_adapter_options(name))) for name in names])
        keymap_names = CottList(values=[keymap.name for keymap in builtin_keymaps()])
        problems: list[str] = []
        for file in files:
            for problem in validate_config_file(file, option_sets, harlequin_option_names(), keymap_names):
                key = problem.key
                problems.append(f"{problem.path}: {key.value}: {problem.message}" if isinstance(key, Some) else f"{problem.path}: {problem.message}")
        if problems:
            return ("\n".join(problems) + "\n").encode("utf-8"), "", 2
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
        schema: dict[str, object] = {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "Harlequin configuration", "type": "object", "additionalProperties": False, "properties": {"default_profile": {"type": "string"}, "profiles": {"type": "object", "additionalProperties": {"type": "object", "properties": properties}}, "keymaps": {"type": "object", "additionalProperties": {"type": "array", "items": binding_schema}}}}
        return (json.dumps(schema, indent=2) + "\n").encode("utf-8"), "", 0
    if mode_name == "init":
        requested = arguments.profile
        if not isinstance(requested, Some):
            return _usage("--config init needs -P NAME to name the profile it writes.")
        if requested.value == "None":
            return _usage("'None' is not allowed as a profile name; pass another name with -P.")
        target = config_path if config_path is not None else cwd / "harlequin.toml"
        entries: list[ConfigEntry] = list(arguments.explicit)
        if adapter_typed:
            entries.insert(0, ConfigEntry(key="adapter", value=ConfigValue_Text(value=adapter_name)))
        if _typed(raw_args, "--limit", ""):
            entries.append(ConfigEntry(key="limit", value=ConfigValue_Integer(value=arguments.limit)))
        if _typed(raw_args, "--output", "-o") and isinstance(arguments.output, Some):
            entries.append(ConfigEntry(key="output", value=ConfigValue_Text(value=arguments.output.value)))
        if _typed(raw_args, "--no-write-history", ""):
            entries.append(ConfigEntry(key="no_write_history", value=ConfigValue_Boolean(value=True)))
        if len(arguments.conn_str) > 0:
            entries.append(ConfigEntry(key="conn_str", value=ConfigValue_Array(values=CottList(values=[ConfigValue_Text(value=item) for item in arguments.conn_str]))))
        existing = read_config_file(target)
        if not isinstance(existing, Ok):
            return _config_failure(existing.error)
        previous = existing.value
        default_profile: Option[str] = previous.value.default_profile if isinstance(previous, Some) else Nothing()
        written = write_profile(target, Profile(name=requested.value, entries=CottList(values=entries)), default_profile)
        if not isinstance(written, Ok):
            return _config_failure(written.error)
        return b"", f"note: wrote profile '{requested.value}' to {written.value}\n", 0
    return _usage(f"unknown --config mode {mode_name}")


def _open_tunnel(values: dict[str, ConfigValue]) -> tuple[SshTunnel | None, str, str | None]:
    host = _text_value(values.get("ssh_host"))
    if host is None or host == "":
        return None, "", None
    raw_timeout = _text_value(values.get("ssh_timeout"))
    try:
        timeout = float(raw_timeout) if raw_timeout is not None else 10.0
    except ValueError:
        return None, "", f"Invalid ssh_timeout value: {raw_timeout}"
    settings = SshSettings(host=host, forwards=CottList(values=_texts(values.get("ssh_forward"))), batch_mode=_truthy(values.get("ssh_batch_mode")), allow_reuse=_truthy(values.get("ssh_allow_reuse")), timeout_seconds=timeout)
    opened = open_ssh_tunnel(settings)
    if isinstance(opened, Ok):
        tunnel = opened.value
        return tunnel, "".join(f"note: {warning}\n" for warning in tunnel.warnings), None
    return None, "", opened.error.message


def _stop_tunnel(tunnel: SshTunnel | None) -> None:
    if tunnel is None or tunnel.process.tag != "harlequin.ssh_process":
        return
    process = cast(subprocess.Popen[str], tunnel.process.unwrap())
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def _cold(args: list[str], env: dict[str, str], environment: FrozenMap[str, str], descriptors: list[AdapterDescriptor], pre_stdin: str | None) -> tuple[bytes, str, I64]:
    scanned = first_pass(CottList(values=args))
    home = Path.home()
    cwd = Path.cwd()
    paths = harlequin_paths(sys.platform, home, environment)
    config_path: Path | None = None
    if isinstance(scanned.config_path, Some):
        config_path = Path(scanned.config_path.value).expanduser()
    elif env.get("HARLEQUIN_CONFIG_PATH", "") != "":
        config_path = Path(env["HARLEQUIN_CONFIG_PATH"]).expanduser()
    explicit_path: Option[Path] = Some(value=config_path) if config_path is not None else Nothing()
    files: list[ConfigFile] = []
    for path in config_search_paths(explicit_path, cwd, paths.config_dir, home):
        read = read_config_file(path)
        if not isinstance(read, Ok):
            return _config_failure(read.error)
        if isinstance(read.value, Some):
            files.append(read.value.value)
    merged = merge_config_files(CottList(values=files))
    profile: Profile | None = None
    profile_error: ConfigError | None = None
    selected = select_profile(merged, scanned.profile)
    if isinstance(selected, Ok):
        chosen = selected.value
        if isinstance(chosen, Some):
            source: Option[str] = Nothing()
            for item in merged.sources:
                if item.name == chosen.value.name:
                    source = Some(value=item.path)
                    break
            interpolated = interpolate_profile(chosen.value, environment, source)
            if isinstance(interpolated, Ok):
                profile = interpolated.value
            else:
                profile_error = interpolated.error
    else:
        profile_error = selected.error
    names = [descriptor.name for descriptor in descriptors]
    adapter_typed = isinstance(scanned.adapter, Some)
    adapter_name = "duckdb"
    if isinstance(scanned.adapter, Some):
        adapter_name = scanned.adapter.value
    elif profile is not None:
        for entry in profile.entries:
            if entry.key == "adapter" and isinstance(entry.value, ConfigValue_Text):
                adapter_name = entry.value.value.lower()
    known = adapter_name in names
    options = _adapter_options(adapter_name) if known else []
    parsed = parse_hsql_arguments(CottList(values=args), CottList(values=names), CottList(values=options))
    if not isinstance(parsed, Ok):
        return b"", hsql_error_line(parsed.error), hsql_exit_status(parsed.error)
    arguments = parsed.value
    descriptor = descriptors[names.index(adapter_name)] if known else descriptors[0]
    if arguments.show_help:
        selected_descriptor: Option[AdapterDescriptor] = Some(value=descriptor) if known else Nothing()
        return hsql_help(CottList(values=descriptors), selected_descriptor, CottList(values=options)).encode("utf-8"), "", 0
    if arguments.show_version:
        return f"hsql, version {HARLEQUIN_VERSION}\n".encode("utf-8"), "", 0
    mode = arguments.mode
    if not known and not isinstance(mode, (HsqlMode_ConfigMode, HsqlMode_Spec, HsqlMode_Info, HsqlMode_Skill)):
        return _usage(f"Profile sets adapter to '{adapter_name}', which is not an installed adapter.")
    if profile_error is not None and not isinstance(mode, (HsqlMode_ConfigMode, HsqlMode_Spec, HsqlMode_Skill)):
        return _config_failure(profile_error)
    values: dict[str, ConfigValue] = {}
    if profile is not None:
        for entry in profile.entries:
            if entry.key not in ("theme", "keymap_name", "show_files", "show_s3", "locale", "viewer_max_rows", "no_download_tzdata"):
                values[entry.key] = entry.value
    for entry in arguments.explicit:
        values[entry.key] = entry.value
    conn = list(arguments.conn_str)
    if not conn:
        conn = _texts(values.get("conn_str"))
    read_only = arguments.read_only or _truthy(values.get("read_only"))
    if not _typed(args, "--limit", ""):
        profile_limit = values.get("limit")
        if isinstance(profile_limit, ConfigValue_Integer) and profile_limit.value >= -1:
            arguments = dataclasses.replace(arguments, limit=profile_limit.value)
    if not _typed(args, "--output", "-o"):
        output = _text_value(values.get("output"))
        if output is not None:
            arguments = dataclasses.replace(arguments, output=Some(value=output))
    if _truthy(values.get("no_write_history")):
        arguments = dataclasses.replace(arguments, write_history=False)
    settings: list[AdapterSetting] = []
    secrets = _connection_secrets(conn)
    for option in options:
        key = _key(option)
        value = values.get(key)
        if value is None:
            continue
        setting = _setting(option, value)
        if setting is None:
            continue
        settings.append(AdapterSetting(name=key, value=setting))
        if option.secret:
            secrets.extend(_texts(value) if isinstance(value, ConfigValue_Array) else [_text_value(value) or ""])
    request = ConnectionRequest(adapter=_kind(adapter_name), conn_str=CottList(values=conn), read_only=read_only, settings=CottList(values=settings))
    context = HsqlContext(profile=Some(value=profile.name) if profile is not None else Nothing(), adapter_name=adapter_name, query_log=paths.query_log, stdout_tty=sys.stdout.isatty(), stderr_tty=sys.stderr.isatty(), no_color="NO_COLOR" in env, implements_cancel=descriptor.implements_cancel, implements_catalog_search=descriptor.implements_catalog_search, secrets=CottList(values=[secret for secret in secrets if secret]))
    if isinstance(mode, (HsqlMode_History, HsqlMode_HistorySearch)):
        narrow = isinstance(scanned.profile, Some) or adapter_typed or len(arguments.conn_str) > 0
        connection_filter: Option[str] = Some(value=_guess_connection_id(adapter_name, conn, values)) if narrow else Nothing()
        term = mode.term if isinstance(mode, HsqlMode_HistorySearch) else ""
        stdout, stderr, status = _history(arguments, cwd, context, connection_filter, term)
        return stdout, redact_text(stderr, context.secrets), status
    if isinstance(mode, HsqlMode_ConfigMode):
        stdout, stderr, status = _config_mode(mode.name, arguments, args, merged, files, names, adapter_name, adapter_typed, config_path, cwd)
        return stdout, redact_text(stderr, context.secrets), status
    if isinstance(mode, HsqlMode_Spec):
        hsql_options: dict[str, object] = {}
        for flags, metavar, help_text in _hsql_option_rows():
            hsql_options[flags] = {"metavar": metavar, "help": help_text}
        adapters: dict[str, object] = {}
        for name in names:
            if not adapter_typed or name == adapter_name:
                adapters[name] = [_option_json(option) for option in _adapter_options(name)]
        return (json.dumps({"hsql": hsql_options, "adapters": adapters}, indent=2) + "\n").encode("utf-8"), "", 0
    if isinstance(mode, HsqlMode_Info):
        capabilities: dict[str, object] = {}
        for item in descriptors:
            capabilities[item.name] = {"display_name": item.display_name, "distribution": item.distribution, "read_only": item.implements_read_only, "cancel": item.implements_cancel, "catalog_search": item.implements_catalog_search, "validate_sql": item.implements_validate_sql}
        info: dict[str, object] = {"version": HARLEQUIN_VERSION, "python": sys.version.split()[0], "config_files": [file.path for file in files], "profile": profile.name if profile is not None else None, "adapters": capabilities}
        return (json.dumps(info, indent=2) + "\n").encode("utf-8"), "", 0
    if isinstance(mode, HsqlMode_Skill):
        if isinstance(arguments.output, Some):
            target = _resolve(cwd, arguments.output.value)
            if target.is_dir() or arguments.output.value.endswith(("/", os.sep)):
                target = target / "SKILL.md"
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(_SKILL, encoding="utf-8")
            except OSError as error:
                return b"", redact_text(f"hsql: error: could not write {target}: {error}\n", context.secrets), 2
            return b"", redact_text(f"note: wrote {target}\n", context.secrets), 0
        return _SKILL.encode("utf-8"), "", 0
    if isinstance(mode, (HsqlMode_SessionReset, HsqlMode_SessionStatus)):
        return _usage("this option needs a running session: pass --session NAME or set HSQL_SESSION.")
    if isinstance(mode, HsqlMode_Execute) and len(arguments.sources) == 0:
        return _usage("no SQL to run. Pass -c/--command or -f/--file, or see 'hsql --help'.")
    tunnel, notes, tunnel_error = _open_tunnel(values)
    if tunnel_error is not None:
        return b"", redact_text(f"hsql: error: {tunnel_error}\n", context.secrets), 3
    try:
        if isinstance(mode, HsqlMode_Serve):
            status = serve_hsql_session(mode.name, request, context, arguments, environment)
            return b"", redact_text(notes, context.secrets), status
        connected = connect(request)
        if not isinstance(connected, Ok):
            failure = connected.error
            if isinstance(failure, ConnectionError_ReadOnlyUnsupported):
                message = f"Harlequin could not connect read-only.\nThe {failure.adapter} adapter does not support read-only connections."
            else:
                message = f"{failure.title}\n{failure.message}"
            return b"", redact_text(notes + f"hsql: error: {message}\n", context.secrets), 3
        connection = connected.value
        try:
            stdin_text: Option[str] = Nothing()
            if any(isinstance(source, SqlSource_SqlFile) and source.path == "-" for source in arguments.sources):
                stdin_text = Some(value=pre_stdin if pre_stdin is not None else sys.stdin.read())
            response = execute_hsql_request(connection, arguments, cwd, stdin_text, context)
        finally:
            close_connection(connection)
        return response.stdout, redact_text(notes + response.stderr, context.secrets), response.status
    finally:
        _stop_tunnel(tunnel)


def _main(args: list[str]) -> tuple[bytes, str, I64]:
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
    stdin_text: Option[str] = Some(value=pre_stdin) if pre_stdin is not None else Nothing()
    sent = send_session_request(name, CottList(values=args), Path.cwd(), stdin_text, environment, sys.stdout.isatty(), sys.stderr.isatty())
    if isinstance(sent, Ok):
        return sent.value.stdout, sent.value.stderr, sent.value.status
    failure = sent.error
    if from_env and isinstance(failure, HsqlError_Connection) and failure.message.startswith("no session named"):
        stdout, stderr, status = _cold(args, env, environment, descriptors, pre_stdin)
        return stdout, f"note: HSQL_SESSION={name} is not running; running cold.\n" + stderr, status
    return b"", hsql_error_line(failure), hsql_exit_status(failure)


def run_hsql(arguments: CottList[str]) -> Never:
    try:
        stdout, stderr, status = _main(list(arguments))
    except KeyboardInterrupt:
        stdout, stderr, status = b"", hsql_error_line(HsqlError_Interrupted()), 130
    except Exception:
        stdout, stderr, status = b"", hsql_error_line(HsqlError_Crash(message="An unexpected exception occurred.")), 70
    if stdout:
        sys.stdout.buffer.write(stdout)
    sys.stdout.flush()
    if stderr:
        sys.stderr.write(stderr)
        sys.stderr.flush()
    sys.exit(status)
