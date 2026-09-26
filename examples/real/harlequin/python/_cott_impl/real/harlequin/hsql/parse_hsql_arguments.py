from typing import Final

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some

from real.harlequin.adapters_types import AdapterOption, OptionKind_Choice, OptionKind_Flag, OptionKind_Repeated
from real.harlequin.config_types import ConfigEntry, ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Real, ConfigValue_Text
from real.harlequin.hsql_types import HsqlArguments, HsqlError, HsqlError_Usage, HsqlMode, HsqlMode_Catalog, HsqlMode_CatalogSearch, HsqlMode_ConfigMode, HsqlMode_Execute, HsqlMode_History, HsqlMode_HistorySearch, HsqlMode_Info, HsqlMode_Serve, HsqlMode_SessionReset, HsqlMode_SessionStatus, HsqlMode_Skill, HsqlMode_Spec, SqlSource, SqlSource_Command, SqlSource_SqlFile

_VALUE_KINDS: Final[str] = "adapter command file text format float_pos float_nonneg int choice array entry_text entry_float entry_choice mode_value"
_MODES: Final[str] = "--catalog --catalog-search --history --history-search --config --spec --info --skill --serve --session-reset --session-status"
_PER_REQUEST: Final[str] = "--session --output --format --csv --json --jsonl --markdown --vertical --tuples-only --no-align --no-header --no-footer --null-string --timeout --limit --display-rows --result --on-error --stats --queue-timeout"
_SERVER_ONLY: Final[str] = "--idle-timeout --max-lifetime"
_FORMATS: Final[str] = "table markdown md vertical csv tsv json jsonl ndjson parquet orc feather arrow none"


def _usage(message: str) -> Result[HsqlArguments, HsqlError]:
    return Err(error=HsqlError_Usage(message=message))


def _names(spec: tuple[list[str], str, str, list[str]]) -> str:
    return " / ".join(f"'{n}'" for n in spec[0])


def _core_specs(adapter_names: list[str]) -> list[tuple[list[str], str, str, list[str]]]:
    formats: list[str] = [str(f) for f in _FORMATS.split()]
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
    names = [n for n in [f"--{option.name}"] + [str(d) for d in option.short_decls] if n not in taken]
    key = option.name.replace("-", "_")
    kind = option.kind
    if isinstance(kind, OptionKind_Flag):
        return (names, key, "entry_flag", [])
    if isinstance(kind, OptionKind_Repeated):
        return (names, key, "array", [])
    if isinstance(kind, OptionKind_Choice):
        return (names, key, "entry_choice", [str(c) for c in kind.choices])
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
    return HsqlMode_SessionStatus()


def parse_hsql_arguments(arguments: CottList[str], adapter_names: CottList[str], adapter_options: CottList[AdapterOption]) -> Result[HsqlArguments, HsqlError]:
    specs = _core_specs([str(n) for n in adapter_names])
    taken: set[str] = {name for spec in specs for name in spec[0]}
    for option in adapter_options:
        spec = _adapter_spec(option, taken)
        if spec[0]:
            specs.append(spec)
            taken.update(spec[0])
    table: dict[str, int] = {}
    for index, spec in enumerate(specs):
        for name in spec[0]:
            if name not in table:
                table[name] = index
    value_kinds = _VALUE_KINDS.split()
    args = [str(a) for a in arguments]
    occurrences: list[tuple[int, str, str]] = []
    conn_str: list[str] = []
    i = 0
    n = len(args)
    while i < n:
        arg = args[i]
        i += 1
        if arg == "--":
            conn_str.extend(args[i:])
            break
        if not (arg.startswith("-") and len(arg) > 1):
            conn_str.append(arg)
            continue
        if "=" in arg and arg.startswith("--"):
            name, explicit_value = arg.split("=", 1)
            has_explicit = True
        else:
            name, explicit_value, has_explicit = arg, "", False
        if name in table:
            index = table[name]
            if specs[index][2] in value_kinds:
                if has_explicit:
                    value = explicit_value
                elif i < n:
                    value = args[i]
                    i += 1
                else:
                    return _usage(f"Option '{name}' requires an argument.")
                occurrences.append((index, value, name))
            else:
                if has_explicit:
                    return _usage(f"Option '{name}' does not take a value.")
                occurrences.append((index, "", name))
            continue
        if arg.startswith("--"):
            return _usage(f"No such option: {name}")
        j = 1
        while j < len(arg):
            opt = "-" + arg[j]
            if opt not in table:
                return _usage(f"No such option: {opt}")
            index = table[opt]
            if specs[index][2] in value_kinds:
                rest = arg[j + 1:]
                if rest:
                    value = rest
                elif i < n:
                    value = args[i]
                    i += 1
                else:
                    return _usage(f"Option '{opt}' requires an argument.")
                occurrences.append((index, value, opt))
                break
            occurrences.append((index, "", opt))
            j += 1

    grouped: dict[int, list[str]] = {}
    for index, value, _spelling in occurrences:
        grouped.setdefault(index, []).append(value)

    adapter: str | None = None
    texts: dict[str, str] = {}
    bools: set[str] = set()
    floats: dict[str, float] = {}
    ints: dict[str, int] = {}
    format_name = "table"
    explicit: list[ConfigEntry] = []
    for index, values in grouped.items():
        spec = specs[index]
        key = spec[1]
        kind = spec[2]
        last = values[-1]
        if kind == "command" or kind == "file":
            continue
        if kind in ("choice", "format", "adapter", "entry_choice") or (kind == "mode_value" and spec[3]):
            match = [c for c in spec[3] if c.casefold() == last.casefold()]
            if not match:
                choices = ", ".join(f"'{c}'" for c in spec[3])
                return _usage(f"Invalid value for {_names(spec)}: '{last}' is not one of {choices}.")
            last = match[0]
        if kind in ("float_pos", "float_nonneg", "entry_float"):
            try:
                real = float(last)
            except ValueError:
                return _usage(f"Invalid value for {_names(spec)}: '{last}' is not a valid float.")
            if kind == "float_nonneg":
                if not real >= 0:
                    return _usage(f"Invalid value for {_names(spec)}: {real} is not in the range x>=0.")
            elif not real > 0:
                return _usage(f"Invalid value for {_names(spec)}: {real} is not in the range x>0.")
            if kind == "entry_float":
                explicit.append(ConfigEntry(key=key, value=ConfigValue_Real(value=real)))
            else:
                floats[key] = real
            continue
        if kind == "int":
            try:
                number = int(last)
            except ValueError:
                return _usage(f"Invalid value for {_names(spec)}: '{last}' is not a valid integer.")
            if number < -1:
                return _usage(f"Invalid value for {_names(spec)}: {number} is not in the range x>=-1.")
            ints[key] = number
            continue
        converted: ConfigValue
        if kind == "adapter":
            adapter = last.lower()
        elif kind == "format":
            format_name = last.lower()
        elif kind == "shorthand":
            format_name = key
        elif kind in ("bool", "mode"):
            bools.add(key)
        elif kind in ("text", "mode_value", "choice"):
            texts[key] = last
        elif kind == "entry_flag":
            converted = ConfigValue_Boolean(value=True)
            explicit.append(ConfigEntry(key=key, value=converted))
        elif kind == "array":
            converted = ConfigValue_Array(values=CottList(values=[ConfigValue_Text(value=v) for v in values]))
            explicit.append(ConfigEntry(key=key, value=converted))
        else:
            explicit.append(ConfigEntry(key=key, value=ConfigValue_Text(value=last)))

    sources: list[SqlSource] = []
    mode: HsqlMode = HsqlMode_Execute()
    first_mode: str | None = None
    first_format: str | None = None
    first_format_kind = ""
    has_source = False
    typed: list[str] = []
    for index, value, spelling in occurrences:
        spec = specs[index]
        long_name = spec[0][0]
        if long_name not in typed:
            typed.append(long_name)
        if spec[2] == "command":
            sources.append(SqlSource_Command(sql=value))
            has_source = True
        elif spec[2] == "file":
            sources.append(SqlSource_SqlFile(path=value))
            has_source = True
        if long_name in _MODES.split() and spec[2] in ("mode", "mode_value"):
            if first_mode is not None and first_mode != spelling:
                return _usage(f"{first_mode} and {spelling} can't be used together.")
            first_mode = spelling
            mode = _mode_of(spec[1], texts.get(spec[1], ""))
        if spec[2] in ("format", "shorthand"):
            if first_format is None:
                first_format = spelling
                first_format_kind = spec[2]
            elif first_format != spelling and (spec[2] == "shorthand" or first_format_kind == "shorthand"):
                return _usage(f"{first_format} and {spelling} both choose an output format; pass only one.")
    if first_mode is not None and has_source:
        return _usage(f"{first_mode} doesn't run SQL, so it can't be combined with -c/--command or -f/--file.")
    if "path" in texts and not isinstance(mode, (HsqlMode_Catalog, HsqlMode_CatalogSearch)):
        return _usage("--path only applies to --catalog and --catalog-search.")
    if isinstance(mode, HsqlMode_CatalogSearch) and not mode.term.strip():
        return _usage("--catalog-search needs a term to search for.")
    if isinstance(mode, HsqlMode_HistorySearch) and not mode.term.strip():
        return _usage("--history-search needs a term to search for.")
    if isinstance(mode, HsqlMode_Serve):
        for long_name in typed:
            if long_name in _PER_REQUEST.split():
                return _usage(f"{long_name} is a per-request option; pass it with each --session request, not to --serve.")
    else:
        for long_name in typed:
            if long_name in _SERVER_ONLY.split():
                return _usage(f"{long_name} only applies to --serve.")
    result = texts.get("result", "all")
    lowered = result.strip().lower()
    if lowered in ("all", "last"):
        result = lowered
    elif lowered.isdigit() and int(lowered) >= 1:
        result = str(int(lowered))
    else:
        return _usage("--result must be all, last, or a result number.")

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
        read_only=any(e.key == "read_only" for e in explicit),
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
