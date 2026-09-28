from typing import Final

from cott_runtime import CottList, Err, F64, I64, Nothing, Ok, Result, Some
from real.harlequin.adapters_types import AdapterOption, OptionKind_Choice, OptionKind_Flag, OptionKind_Repeated
from real.harlequin.config_types import ConfigEntry, ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Real, ConfigValue_Text
from real.harlequin.hsql_types import HsqlArguments, HsqlError, HsqlError_Usage, HsqlMode, HsqlMode_Catalog, HsqlMode_CatalogSearch, HsqlMode_ConfigMode, HsqlMode_Execute, HsqlMode_History, HsqlMode_HistorySearch, HsqlMode_Info, HsqlMode_Serve, HsqlMode_SessionReset, HsqlMode_SessionStatus, HsqlMode_Skill, HsqlMode_Spec, SqlSource, SqlSource_Command, SqlSource_SqlFile

_FORMATS: Final[str] = "table markdown md vertical csv tsv json jsonl ndjson parquet orc feather arrow none"
_VALUE_KINDS: Final[str] = "adapter command file text format positive_float nonnegative_float integer choice repeated connection_text connection_float connection_choice mode_value"
_PER_REQUEST: Final[str] = "session output format csv json jsonl markdown vertical tuples_only no_align no_header no_footer null_string timeout path limit display_rows result on_error no_write_history stats color queue_timeout"


def _usage(message: str) -> Result[HsqlArguments, HsqlError]:
    return Err(error=HsqlError_Usage(message=message))


def _names(spec: tuple[list[str], str, str, list[str]]) -> str:
    return " / ".join(f"'{name}'" for name in spec[0])


def _core_specs(adapter_names: CottList[str]) -> list[tuple[list[str], str, str, list[str]]]:
    format_choices: list[str] = []
    format_choices.extend(_FORMATS.split())
    return [
        (["--adapter", "-a"], "adapter", "adapter", [name for name in adapter_names]),
        (["--command", "-c"], "", "command", []),
        (["--file", "-f"], "", "file", []),
        (["--output", "-o"], "output", "text", []),
        (["--format"], "format", "format", format_choices),
        (["--csv"], "csv", "shorthand", []),
        (["--json"], "json", "shorthand", []),
        (["--jsonl"], "jsonl", "shorthand", []),
        (["--markdown"], "markdown", "shorthand", []),
        (["--vertical", "-x"], "vertical", "shorthand", []),
        (["--tuples-only", "-t"], "tuples_only", "flag", []),
        (["--no-align", "-A"], "no_align", "flag", []),
        (["--no-header"], "no_header", "flag", []),
        (["--no-footer"], "no_footer", "flag", []),
        (["--null-string"], "null_string", "text", []),
        (["--profile", "-P"], "profile", "text", []),
        (["--config-path"], "config_path", "text", []),
        (["--read-only", "-r"], "read_only", "connection_flag", []),
        (["--timeout"], "timeout", "positive_float", []),
        (["--ssh-host"], "ssh_host", "connection_text", []),
        (["--ssh-forward"], "ssh_forward", "repeated", []),
        (["--ssh-batch-mode"], "ssh_batch_mode", "connection_flag", []),
        (["--ssh-allow-reuse"], "ssh_allow_reuse", "connection_flag", []),
        (["--ssh-timeout"], "ssh_timeout", "connection_float", []),
        (["--catalog"], "catalog", "mode", []),
        (["--catalog-search"], "catalog_search", "mode_value", []),
        (["--path"], "path", "text", []),
        (["--history"], "history", "mode", []),
        (["--history-search"], "history_search", "mode_value", []),
        (["--config"], "config", "mode_value", ["show", "list-profiles", "validate", "schema", "init"]),
        (["--spec"], "spec", "mode", []),
        (["--info"], "info", "mode", []),
        (["--skill"], "skill", "mode", []),
        (["--limit"], "limit", "integer", []),
        (["--display-rows"], "display_rows", "integer", []),
        (["--result"], "result", "text", []),
        (["--on-error"], "on_error", "choice", ["stop", "continue"]),
        (["--no-write-history"], "no_write_history", "flag", []),
        (["--stats"], "stats", "flag", []),
        (["--color"], "color", "choice", ["auto", "always", "never"]),
        (["--serve"], "serve", "mode_value", []),
        (["--session"], "session", "text", []),
        (["--session-reset"], "session_reset", "mode", []),
        (["--session-status"], "session_status", "mode", []),
        (["--queue-timeout"], "queue_timeout", "positive_float", []),
        (["--idle-timeout"], "idle_timeout", "nonnegative_float", []),
        (["--max-lifetime"], "max_lifetime", "nonnegative_float", []),
        (["--help"], "help", "flag", []),
        (["--version"], "version", "flag", []),
    ]


def _adapter_spec(option: AdapterOption, taken: set[str]) -> tuple[list[str], str, str, list[str]]:
    names: list[str] = []
    long_name = "--" + option.name
    if long_name not in taken:
        names.append(long_name)
    for short_name in option.short_decls:
        if short_name not in taken and short_name not in names:
            names.append(short_name)
    key = option.name.replace("-", "_")
    if isinstance(option.kind, OptionKind_Flag):
        return names, key, "connection_flag", []
    if isinstance(option.kind, OptionKind_Repeated):
        return names, key, "repeated", []
    if isinstance(option.kind, OptionKind_Choice):
        return names, key, "connection_choice", [choice for choice in option.kind.choices]
    return names, key, "connection_text", []


def _mode(key: str, value: str) -> HsqlMode:
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
    return HsqlMode_SessionStatus()


def _result_number(value: str) -> str | None:
    lowered = value.strip().lower()
    if lowered in ("all", "last"):
        return lowered
    if lowered.isascii() and lowered.isdecimal():
        number = lowered.lstrip("0")
        if number:
            return number
    return None


def parse_hsql_arguments(arguments: CottList[str], adapter_names: CottList[str], adapter_options: CottList[AdapterOption]) -> Result[HsqlArguments, HsqlError]:
    specs = _core_specs(adapter_names)
    taken = {name for spec in specs for name in spec[0]}
    for option in adapter_options:
        spec = _adapter_spec(option, taken)
        if spec[0]:
            specs.append(spec)
            taken.update(spec[0])
    lookup: dict[str, int] = {}
    for index, spec in enumerate(specs):
        for name in spec[0]:
            lookup[name] = index
    multi_short = sorted((name for name in lookup if name.startswith("-") and not name.startswith("--") and len(name) > 2), key=len, reverse=True)
    value_kinds = set(_VALUE_KINDS.split())

    seen: dict[int, None] = {}
    connection_values: dict[int, ConfigValue] = {}
    connection_lists: dict[int, list[str]] = {}
    connection_order: dict[int, None] = {}
    texts: dict[str, str] = {}
    numbers: dict[str, I64] = {}
    floats: dict[str, F64] = {}
    flags: set[str] = set()
    conn_str: list[str] = []
    sources: list[SqlSource] = []
    mode: HsqlMode = HsqlMode_Execute()
    first_mode: int | None = None
    first_mode_name: str | None = None
    first_format: int | None = None
    first_format_name: str | None = None
    first_format_kind = ""
    adapter: str | None = None
    format_name = "table"
    selected_result = "all"
    read_only = False
    count = len(arguments)
    i = 0
    while i < count:
        arg = arguments[i]
        i += 1
        if arg == "--":
            while i < count:
                conn_str.append(arguments[i])
                i += 1
            break
        if len(arg) <= 1 or not arg.startswith("-"):
            conn_str.append(arg)
            continue

        occurrences: list[tuple[int, str, str]] = []
        name, separator, attached = arg.partition("=") if arg.startswith("--") else (arg, "", "")
        if name in lookup:
            index = lookup[name]
            if specs[index][2] in value_kinds:
                if separator:
                    value = attached
                elif i < count:
                    value = arguments[i]
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
                short_name = "-" + arg[j]
                for candidate in multi_short:
                    if arg.startswith(candidate[1:], j):
                        short_name = candidate
                        break
                if short_name not in lookup:
                    return _usage(f"No such option: {short_name}")
                index = lookup[short_name]
                j += len(short_name) - 1
                if specs[index][2] in value_kinds:
                    if j < len(arg):
                        value = arg[j:]
                    elif i < count:
                        value = arguments[i]
                        i += 1
                    else:
                        return _usage(f"Option '{short_name}' requires an argument.")
                    occurrences.append((index, value, short_name))
                    break
                occurrences.append((index, "", short_name))

        for index, value, spelling in occurrences:
            spec = specs[index]
            key = spec[1]
            kind = spec[2]
            seen[index] = None
            if kind in ("adapter", "format", "choice", "connection_choice") or (kind == "mode_value" and spec[3]):
                match: str | None = None
                for choice in spec[3]:
                    if choice.casefold() == value.casefold():
                        match = choice
                        break
                if match is None:
                    choices = ", ".join(f"'{choice}'" for choice in spec[3])
                    return _usage(f"Invalid value for {_names(spec)}: '{value}' is not one of {choices}.")
                value = match
            if kind == "integer":
                try:
                    number = int(value)
                except ValueError:
                    return _usage(f"Invalid value for {_names(spec)}: '{value}' is not a valid integer.")
                if number < -1:
                    return _usage(f"Invalid value for {_names(spec)}: {number} is not in the range x>=-1.")
                numbers[key] = number
                continue
            if kind in ("positive_float", "nonnegative_float", "connection_float"):
                try:
                    real = float(value)
                except ValueError:
                    return _usage(f"Invalid value for {_names(spec)}: '{value}' is not a valid float.")
                if kind == "nonnegative_float":
                    if not real >= 0:
                        return _usage(f"Invalid value for {_names(spec)}: {real} is not in the range x>=0.")
                elif not real > 0:
                    return _usage(f"Invalid value for {_names(spec)}: {real} is not in the range x>0.")
                if kind == "connection_float":
                    connection_order[index] = None
                    connection_values[index] = ConfigValue_Real(value=real)
                else:
                    floats[key] = real
                continue
            if kind in ("command", "file"):
                if first_mode_name is not None:
                    return _usage(f"{first_mode_name} doesn't run SQL, so it can't be combined with -c/--command or -f/--file.")
                if kind == "command":
                    sources.append(SqlSource_Command(sql=value))
                else:
                    sources.append(SqlSource_SqlFile(path=value))
                continue
            if kind in ("mode", "mode_value"):
                if first_mode is not None and first_mode != index:
                    return _usage(f"{first_mode_name} and {spelling} can't be used together.")
                if sources:
                    return _usage(f"{spelling} doesn't run SQL, so it can't be combined with -c/--command or -f/--file.")
                if key == "catalog_search" and not value.strip():
                    return _usage("--catalog-search needs a term to search for.")
                if key == "history_search" and not value.strip():
                    return _usage("--history-search needs a term to search for.")
                if first_mode is None:
                    first_mode = index
                    first_mode_name = spelling
                mode = _mode(key, value)
                continue
            if kind in ("format", "shorthand"):
                if first_format is not None and first_format != index and (kind == "shorthand" or first_format_kind == "shorthand"):
                    return _usage(f"{first_format_name} and {spelling} both choose an output format; pass only one.")
                if first_format is None:
                    first_format = index
                    first_format_name = spelling
                    first_format_kind = kind
                format_name = value.lower() if kind == "format" else key
                continue
            if kind == "adapter":
                adapter = value.lower()
            elif kind == "flag":
                flags.add(key)
            elif kind in ("text", "choice"):
                if key == "result":
                    normalized = _result_number(value)
                    if normalized is None:
                        return _usage("--result must be all, last, or a result number.")
                    selected_result = normalized
                else:
                    texts[key] = value
            elif kind == "connection_flag":
                connection_order[index] = None
                connection_values[index] = ConfigValue_Boolean(value=True)
                if key == "read_only":
                    read_only = True
            elif kind == "repeated":
                connection_order[index] = None
                if index not in connection_lists:
                    connection_lists[index] = []
                connection_lists[index].append(value)
            else:
                connection_order[index] = None
                connection_values[index] = ConfigValue_Text(value=value)

    if "path" in texts and not isinstance(mode, (HsqlMode_Catalog, HsqlMode_CatalogSearch)):
        return _usage("--path only applies to --catalog and --catalog-search.")
    if isinstance(mode, HsqlMode_Serve):
        per_request = set(_PER_REQUEST.split())
        for index in seen:
            if specs[index][1] in per_request:
                return _usage(f"{specs[index][0][0]} is a per-request option; pass it with each --session request, not to --serve.")
    else:
        for index in seen:
            if specs[index][1] in ("idle_timeout", "max_lifetime"):
                return _usage(f"{specs[index][0][0]} only applies to --serve.")

    explicit: list[ConfigEntry] = []
    for index in connection_order:
        if index in connection_lists:
            converted: ConfigValue = ConfigValue_Array(values=CottList(values=[ConfigValue_Text(value=item) for item in connection_lists[index]]))
        else:
            converted = connection_values[index]
        explicit.append(ConfigEntry(key=specs[index][1], value=converted))
    output = texts.get("output")
    null_string = texts.get("null_string")
    profile = texts.get("profile")
    config_path = texts.get("config_path")
    catalog_path = texts.get("path")
    session = texts.get("session")
    timeout = floats.get("timeout")
    queue_timeout = floats.get("queue_timeout")
    display_rows = numbers.get("display_rows")
    return Ok(value=HsqlArguments(
        adapter=Some(value=adapter) if adapter is not None else Nothing(),
        conn_str=CottList(values=conn_str),
        sources=CottList(values=sources),
        mode=mode,
        output=Some(value=output) if output is not None else Nothing(),
        format=format_name,
        tuples_only="tuples_only" in flags,
        no_align="no_align" in flags,
        no_header="no_header" in flags,
        no_footer="no_footer" in flags,
        null_string=Some(value=null_string) if null_string is not None else Nothing(),
        profile=Some(value=profile) if profile is not None else Nothing(),
        config_path=Some(value=config_path) if config_path is not None else Nothing(),
        read_only=read_only,
        timeout_seconds=Some(value=timeout) if timeout is not None else Nothing(),
        catalog_path=Some(value=catalog_path) if catalog_path is not None else Nothing(),
        limit=numbers.get("limit", 500),
        display_rows=Some(value=display_rows) if display_rows is not None else Nothing(),
        result=selected_result,
        continue_on_error=texts.get("on_error", "stop") == "continue",
        write_history="no_write_history" not in flags,
        stats="stats" in flags,
        color=texts.get("color", "never"),
        session=Some(value=session) if session is not None else Nothing(),
        queue_timeout_seconds=Some(value=queue_timeout) if queue_timeout is not None else Nothing(),
        idle_timeout_seconds=floats.get("idle_timeout", 1800.0),
        max_lifetime_seconds=floats.get("max_lifetime", 28800.0),
        explicit=CottList(values=explicit),
        show_help="help" in flags,
        show_version="version" in flags,
    ))
