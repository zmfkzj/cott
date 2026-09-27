from typing import Final

from cott_runtime import CottList, Err, F64, I64, Nothing, Ok, Result, Some

from real.harlequin.adapters_types import AdapterOption, OptionKind_Choice, OptionKind_Flag, OptionKind_Repeated
from real.harlequin.config_types import ConfigEntry, ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Real, ConfigValue_Text
from real.harlequin.hsql_types import HsqlArguments, HsqlError, HsqlError_Usage, HsqlMode, HsqlMode_Catalog, HsqlMode_CatalogSearch, HsqlMode_ConfigMode, HsqlMode_Execute, HsqlMode_History, HsqlMode_HistorySearch, HsqlMode_Info, HsqlMode_Serve, HsqlMode_SessionReset, HsqlMode_SessionStatus, HsqlMode_Skill, HsqlMode_Spec, SqlSource, SqlSource_Command, SqlSource_SqlFile

_VALUE_KINDS: Final[str] = "adapter command file text format float_pos float_nonneg int choice array entry_text entry_float entry_choice mode_value"
_FORMATS: Final[str] = "table markdown md vertical csv tsv json jsonl ndjson parquet orc feather arrow none"
_PER_REQUEST: Final[str] = "session output format csv json jsonl markdown vertical tuples_only no_align no_header no_footer null_string timeout limit display_rows result on_error stats queue_timeout"
_SERVER_ONLY: Final[str] = "idle_timeout max_lifetime"


def _usage(message: str) -> Result[HsqlArguments, HsqlError]:
    return Err(error=HsqlError_Usage(message=message))


def _names(spec: tuple[list[str], str, str, list[str]]) -> str:
    return " / ".join(f"'{name}'" for name in spec[0])


def _core_specs(adapter_names: list[str]) -> list[tuple[list[str], str, str, list[str]]]:
    formats: list[str] = []
    formats.extend(_FORMATS.split())
    specs: list[tuple[list[str], str, str, list[str]]] = [
        (["--adapter", "-a"], "adapter", "adapter", adapter_names),
        (["--command", "-c"], "", "command", []),
        (["--file", "-f"], "", "file", []),
        (["--output", "-o"], "output", "text", []),
        (["--format"], "format", "format", formats),
        (["--csv"], "csv", "shorthand", []),
        (["--json"], "json", "shorthand", []),
        (["--jsonl"], "jsonl", "shorthand", []),
        (["--markdown"], "markdown", "shorthand", []),
        (["--vertical", "-x"], "vertical", "shorthand", []),
        (["--tuples-only", "-t"], "tuples_only", "bool", []),
        (["--no-align", "-A"], "no_align", "bool", []),
        (["--no-header"], "no_header", "bool", []),
        (["--no-footer"], "no_footer", "bool", []),
        (["--null-string"], "null_string", "text", []),
        (["--profile", "-P"], "profile", "text", []),
        (["--config-path"], "config_path", "text", []),
        (["--read-only", "-r"], "read_only", "entry_flag", []),
        (["--timeout"], "timeout", "float_pos", []),
        (["--ssh-host"], "ssh_host", "entry_text", []),
        (["--ssh-forward"], "ssh_forward", "array", []),
        (["--ssh-batch-mode"], "ssh_batch_mode", "entry_flag", []),
        (["--ssh-allow-reuse"], "ssh_allow_reuse", "entry_flag", []),
        (["--ssh-timeout"], "ssh_timeout", "entry_float", []),
        (["--catalog"], "catalog", "mode", []),
        (["--catalog-search"], "catalog_search", "mode_value", []),
        (["--path"], "path", "text", []),
        (["--history"], "history", "mode", []),
        (["--history-search"], "history_search", "mode_value", []),
        (["--config"], "config", "mode_value", ["show", "list-profiles", "validate", "schema", "init"]),
        (["--spec"], "spec", "mode", []),
        (["--info"], "info", "mode", []),
        (["--skill"], "skill", "mode", []),
        (["--limit"], "limit", "int", []),
        (["--display-rows"], "display_rows", "int", []),
        (["--result"], "result", "text", []),
        (["--on-error"], "on_error", "choice", ["stop", "continue"]),
        (["--no-write-history"], "no_write_history", "bool", []),
        (["--stats"], "stats", "bool", []),
        (["--color"], "color", "choice", ["auto", "always", "never"]),
        (["--serve"], "serve", "mode_value", []),
        (["--session"], "session", "text", []),
        (["--session-reset"], "session_reset", "mode", []),
        (["--session-status"], "session_status", "mode", []),
        (["--queue-timeout"], "queue_timeout", "float_pos", []),
        (["--idle-timeout"], "idle_timeout", "float_nonneg", []),
        (["--max-lifetime"], "max_lifetime", "float_nonneg", []),
        (["--help"], "help", "bool", []),
        (["--version"], "version", "bool", []),
    ]
    return specs


def _adapter_spec(option: AdapterOption, taken: set[str]) -> tuple[list[str], str, str, list[str]]:
    long_name = f"--{option.name}"
    names: list[str] = []
    if long_name not in taken:
        names.append(long_name)
    for declaration in option.short_decls:
        if declaration not in taken and declaration not in names:
            names.append(declaration)
    key = option.name.replace("-", "_")
    kind = option.kind
    if isinstance(kind, OptionKind_Flag):
        return (names, key, "entry_flag", [])
    if isinstance(kind, OptionKind_Repeated):
        return (names, key, "array", [])
    if isinstance(kind, OptionKind_Choice):
        return (names, key, "entry_choice", list(kind.choices))
    return (names, key, "entry_text", [])


def _mode_of(key: str, value: str) -> HsqlMode:
    if key == "catalog":
        return HsqlMode_Catalog()
    if key == "catalog_search":
        return HsqlMode_CatalogSearch(term=value)
    if key == "history":
        return HsqlMode_History()
    if key == "history_search":
        return HsqlMode_HistorySearch(term=value)
    if key == "config":
        return HsqlMode_ConfigMode(name=value)
    if key == "spec":
        return HsqlMode_Spec()
    if key == "info":
        return HsqlMode_Info()
    if key == "skill":
        return HsqlMode_Skill()
    if key == "serve":
        return HsqlMode_Serve(name=value)
    if key == "session_reset":
        return HsqlMode_SessionReset()
    if key == "session_status":
        return HsqlMode_SessionStatus()
    raise ValueError(f"Unknown hsql mode: {key}")


def _result_value(value: str) -> str | None:
    normalized = value.strip().lower()
    if normalized == "all" or normalized == "last":
        return normalized
    if normalized.isascii() and normalized.isdecimal():
        positive = normalized.lstrip("0")
        if positive:
            return positive
    return None


def parse_hsql_arguments(arguments: CottList[str], adapter_names: CottList[str], adapter_options: CottList[AdapterOption]) -> Result[HsqlArguments, HsqlError]:
    specs = _core_specs(list(adapter_names))
    taken = {name for spec in specs for name in spec[0]}
    for option in adapter_options:
        spec = _adapter_spec(option, taken)
        if spec[0]:
            specs.append(spec)
            taken.update(spec[0])
    table: dict[str, int] = {}
    for index, spec in enumerate(specs):
        for name in spec[0]:
            table[name] = index

    value_kinds = _VALUE_KINDS.split()
    per_request = _PER_REQUEST.split()
    server_only = _SERVER_ONLY.split()
    args = list(arguments)
    occurrences: list[tuple[int, str, str]] = []
    typed: dict[int, None] = {}
    conn_str: list[str] = []
    sources: list[SqlSource] = []
    mode: HsqlMode = HsqlMode_Execute()
    first_mode_index: int | None = None
    first_mode_spelling: str | None = None
    first_format_index: int | None = None
    first_format_spelling: str | None = None
    first_format_kind = ""
    adapter: str | None = None
    format_name = "table"
    result = "all"
    read_only = False
    texts: dict[str, str] = {}
    bools: set[str] = set()
    floats: dict[str, F64] = {}
    ints: dict[str, I64] = {}
    entry_values: dict[int, ConfigValue] = {}
    entry_arrays: dict[int, list[str]] = {}
    explicit_order: dict[int, None] = {}
    i = 0
    while i < len(args):
        arg = args[i]
        i += 1
        if arg == "--":
            conn_str.extend(args[i:])
            break
        if len(arg) <= 1 or not arg.startswith("-"):
            conn_str.append(arg)
            continue

        occurrences.clear()
        if arg.startswith("--"):
            name, separator, attached = arg.partition("=")
        else:
            name, separator, attached = arg, "", ""
        if name in table:
            index = table[name]
            if specs[index][2] in value_kinds:
                if separator:
                    value = attached
                elif i < len(args):
                    value = args[i]
                    i += 1
                else:
                    return _usage(f"Option '{name}' requires an argument.")
                occurrences.append((index, value, name))
            else:
                if separator:
                    return _usage(f"Option '{name}' does not take a value.")
                occurrences.append((index, "", name))
        elif arg.startswith("--"):
            return _usage(f"No such option: {name}")
        else:
            j = 1
            while j < len(arg):
                name = "-" + arg[j]
                if name not in table:
                    return _usage(f"No such option: {name}")
                index = table[name]
                if specs[index][2] in value_kinds:
                    if j + 1 < len(arg):
                        value = arg[j + 1:]
                    elif i < len(args):
                        value = args[i]
                        i += 1
                    else:
                        return _usage(f"Option '{name}' requires an argument.")
                    occurrences.append((index, value, name))
                    break
                occurrences.append((index, "", name))
                j += 1

        for index, value, spelling in occurrences:
            spec = specs[index]
            key = spec[1]
            kind = spec[2]
            typed[index] = None
            if kind in ("choice", "format", "adapter", "entry_choice") or (kind == "mode_value" and spec[3]):
                match = next((choice for choice in spec[3] if choice.casefold() == value.casefold()), None)
                if match is None:
                    choices = ", ".join(f"'{choice}'" for choice in spec[3])
                    return _usage(f"Invalid value for {_names(spec)}: '{value}' is not one of {choices}.")
                value = match
            if kind == "int":
                try:
                    number = int(value)
                except ValueError:
                    return _usage(f"Invalid value for {_names(spec)}: '{value}' is not a valid integer.")
                if number < -1:
                    return _usage(f"Invalid value for {_names(spec)}: {number} is not in the range x>=-1.")
                ints[key] = number
                continue
            if kind in ("float_pos", "float_nonneg", "entry_float"):
                try:
                    real = float(value)
                except ValueError:
                    return _usage(f"Invalid value for {_names(spec)}: '{value}' is not a valid float.")
                if kind == "float_nonneg":
                    if not real >= 0:
                        return _usage(f"Invalid value for {_names(spec)}: {real} is not in the range x>=0.")
                elif not real > 0:
                    return _usage(f"Invalid value for {_names(spec)}: {real} is not in the range x>0.")
                if kind == "entry_float":
                    explicit_order[index] = None
                    entry_values[index] = ConfigValue_Real(value=real)
                else:
                    floats[key] = real
                continue
            if kind == "command" or kind == "file":
                if first_mode_spelling is not None:
                    return _usage(f"{first_mode_spelling} doesn't run SQL, so it can't be combined with -c/--command or -f/--file.")
                if kind == "command":
                    sources.append(SqlSource_Command(sql=value))
                else:
                    sources.append(SqlSource_SqlFile(path=value))
                continue
            if kind == "mode" or kind == "mode_value":
                if first_mode_index is not None and first_mode_index != index:
                    return _usage(f"{first_mode_spelling} and {spelling} can't be used together.")
                if sources:
                    return _usage(f"{spelling} doesn't run SQL, so it can't be combined with -c/--command or -f/--file.")
                if key == "catalog_search" and not value.strip():
                    return _usage("--catalog-search needs a term to search for.")
                if key == "history_search" and not value.strip():
                    return _usage("--history-search needs a term to search for.")
                if first_mode_index is None:
                    first_mode_index = index
                    first_mode_spelling = spelling
                mode = _mode_of(key, value)
                continue
            if kind == "format" or kind == "shorthand":
                if first_format_index is not None and first_format_index != index and (kind == "shorthand" or first_format_kind == "shorthand"):
                    return _usage(f"{first_format_spelling} and {spelling} both choose an output format; pass only one.")
                if first_format_index is None:
                    first_format_index = index
                    first_format_spelling = spelling
                    first_format_kind = kind
                format_name = value.lower() if kind == "format" else key
                continue
            if kind == "adapter":
                adapter = value.lower()
            elif kind == "bool":
                bools.add(key)
            elif kind == "text" or kind == "choice":
                if key == "result":
                    normalized = _result_value(value)
                    if normalized is None:
                        return _usage("--result must be all, last, or a result number.")
                    result = normalized
                else:
                    texts[key] = value
            elif kind == "entry_flag":
                explicit_order[index] = None
                entry_values[index] = ConfigValue_Boolean(value=True)
                if key == "read_only":
                    read_only = True
            elif kind == "array":
                explicit_order[index] = None
                if index not in entry_arrays:
                    entry_arrays[index] = []
                entry_arrays[index].append(value)
            elif kind == "entry_text" or kind == "entry_choice":
                explicit_order[index] = None
                entry_values[index] = ConfigValue_Text(value=value)

    if "path" in texts and not isinstance(mode, (HsqlMode_Catalog, HsqlMode_CatalogSearch)):
        return _usage("--path only applies to --catalog and --catalog-search.")
    if isinstance(mode, HsqlMode_Serve):
        for index in typed:
            if specs[index][1] in per_request:
                return _usage(f"{specs[index][0][0]} is a per-request option; pass it with each --session request, not to --serve.")
    else:
        for index in typed:
            if specs[index][1] in server_only:
                return _usage(f"{specs[index][0][0]} only applies to --serve.")

    explicit: list[ConfigEntry] = []
    for index in explicit_order:
        if index in entry_arrays:
            items: list[ConfigValue] = [ConfigValue_Text(value=item) for item in entry_arrays[index]]
            converted: ConfigValue = ConfigValue_Array(values=CottList(values=items))
        else:
            converted = entry_values[index]
        explicit.append(ConfigEntry(key=specs[index][1], value=converted))
    output = texts.get("output")
    null_string = texts.get("null_string")
    profile = texts.get("profile")
    config_path = texts.get("config_path")
    catalog_path = texts.get("path")
    session = texts.get("session")
    timeout = floats.get("timeout")
    queue_timeout = floats.get("queue_timeout")
    display_rows = ints.get("display_rows")
    return Ok(value=HsqlArguments(
        adapter=Some(value=adapter) if adapter is not None else Nothing(),
        conn_str=CottList(values=conn_str),
        sources=CottList(values=sources),
        mode=mode,
        output=Some(value=output) if output is not None else Nothing(),
        format=format_name,
        tuples_only="tuples_only" in bools,
        no_align="no_align" in bools,
        no_header="no_header" in bools,
        no_footer="no_footer" in bools,
        null_string=Some(value=null_string) if null_string is not None else Nothing(),
        profile=Some(value=profile) if profile is not None else Nothing(),
        config_path=Some(value=config_path) if config_path is not None else Nothing(),
        read_only=read_only,
        timeout_seconds=Some(value=timeout) if timeout is not None else Nothing(),
        catalog_path=Some(value=catalog_path) if catalog_path is not None else Nothing(),
        limit=ints.get("limit", 500),
        display_rows=Some(value=display_rows) if display_rows is not None else Nothing(),
        result=result,
        continue_on_error=texts.get("on_error", "stop") == "continue",
        write_history="no_write_history" not in bools,
        stats="stats" in bools,
        color=texts.get("color", "never"),
        session=Some(value=session) if session is not None else Nothing(),
        queue_timeout_seconds=Some(value=queue_timeout) if queue_timeout is not None else Nothing(),
        idle_timeout_seconds=floats.get("idle_timeout", 1800.0),
        max_lifetime_seconds=floats.get("max_lifetime", 28800.0),
        explicit=CottList(values=explicit),
        show_help="help" in bools,
        show_version="version" in bools,
    ))
