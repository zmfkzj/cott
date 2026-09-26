from typing import Final

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some

from real.harlequin.adapters_types import AdapterOption, OptionKind_Choice, OptionKind_Flag, OptionKind_Repeated
from real.harlequin.cli_types import CliArguments, CliError, CliError_Usage
from real.harlequin.config_types import ConfigEntry, ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Integer, ConfigValue_Real, ConfigValue_Text

_VALUE_KINDS: Final[str] = "profile config_path text int float adapter choice array"

_HSQL_ONLY: Final[str] = "-c --command --file --format --csv --json --jsonl --markdown -x --vertical --tuples-only -A --no-align --no-header --no-footer --null-string --timeout --catalog --catalog-search --path --history --history-search --spec --info --skill --display-rows --result --on-error --stats --color --serve --session --session-reset --session-status --queue-timeout --idle-timeout --max-lifetime"


def _usage(message: str) -> Result[CliArguments, CliError]:
    return Err(error=CliError_Usage(message=message))


def _no_such(name: str) -> Result[CliArguments, CliError]:
    if name in _HSQL_ONLY.split():
        return _usage(f"{name} is not a harlequin option. Did you mean 'hsql {name}'? hsql is Harlequin's headless CLI: it runs SQL and exits. See https://harlequin.sh/docs/headless")
    return _usage(f"No such option: {name}")


def _names(spec: tuple[list[str], str, str, list[str]]) -> str:
    return " / ".join(f"'{n}'" for n in spec[0])


def _core_specs(adapter_names: list[str]) -> list[tuple[list[str], str, str, list[str]]]:
    return [
        (["--profile", "-P"], "", "profile", []),
        (["--config-path"], "", "config_path", []),
        (["--theme", "-t"], "theme", "text", []),
        (["--viewer-max-rows"], "viewer_max_rows", "int", []),
        (["--limit"], "limit", "int", []),
        (["--output", "-o"], "output", "text", []),
        (["--adapter", "-a"], "adapter", "adapter", adapter_names),
        (["--no-write-history"], "no_write_history", "flag", []),
        (["--read-only", "-r"], "read_only", "flag", []),
        (["--show-files", "-f"], "show_files", "text", []),
        (["--show-s3", "--s3"], "show_s3", "text", []),
        (["--keymap-name"], "keymap_name", "array", []),
        (["--ssh-host"], "ssh_host", "text", []),
        (["--ssh-forward"], "ssh_forward", "array", []),
        (["--ssh-batch-mode"], "ssh_batch_mode", "flag", []),
        (["--ssh-allow-reuse"], "ssh_allow_reuse", "flag", []),
        (["--ssh-timeout"], "ssh_timeout", "float", []),
        (["--locale"], "locale", "text", []),
        (["--no-download-tzdata"], "no_download_tzdata", "flag", []),
        (["--config"], "", "wizard", []),
        (["--keys"], "", "keys", []),
        (["--version"], "", "version", []),
        (["--help"], "", "help", []),
    ]


def _adapter_spec(option: AdapterOption) -> tuple[list[str], str, str, list[str]]:
    names = [f"--{option.name}"] + [str(d) for d in option.short_decls]
    key = option.name.replace("-", "_")
    kind = option.kind
    if isinstance(kind, OptionKind_Flag):
        return (names, key, "flag", [])
    if isinstance(kind, OptionKind_Repeated):
        return (names, key, "array", [])
    if isinstance(kind, OptionKind_Choice):
        return (names, key, "choice", [str(c) for c in kind.choices])
    return (names, key, "text", [])


def parse_harlequin_arguments(arguments: CottList[str], adapter_names: CottList[str], adapter_options: CottList[AdapterOption]) -> Result[CliArguments, CliError]:
    specs = _core_specs([str(n) for n in adapter_names])
    for option in adapter_options:
        specs.append(_adapter_spec(option))
    table: dict[str, int] = {}
    for index, spec in enumerate(specs):
        for name in spec[0]:
            if name not in table:
                table[name] = index
    args = [str(a) for a in arguments]
    raw: dict[int, list[str]] = {}
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
        if "=" in arg:
            name, explicit_value = arg.split("=", 1)
            has_explicit = True
        else:
            name, explicit_value, has_explicit = arg, "", False
        if name in table:
            index = table[name]
            if specs[index][2] in _VALUE_KINDS.split():
                if has_explicit:
                    value = explicit_value
                elif i < n:
                    value = args[i]
                    i += 1
                else:
                    return _usage(f"Option '{name}' requires an argument.")
                raw.setdefault(index, []).append(value)
            else:
                if has_explicit:
                    return _usage(f"Option '{name}' does not take a value.")
                raw.setdefault(index, []).append("")
            continue
        if arg.startswith("--"):
            return _no_such(name)
        j = 1
        while j < len(arg):
            opt = "-" + arg[j]
            if opt not in table:
                return _no_such(opt)
            index = table[opt]
            if specs[index][2] in _VALUE_KINDS.split():
                rest = arg[j + 1:]
                if rest:
                    value = rest
                elif i < n:
                    value = args[i]
                    i += 1
                else:
                    return _usage(f"Option '{opt}' requires an argument.")
                raw.setdefault(index, []).append(value)
                break
            raw.setdefault(index, []).append("")
            j += 1
    profile: str | None = None
    config_path: str | None = None
    flags = {"wizard": False, "keys": False, "version": False, "help": False}
    explicit: list[ConfigEntry] = []
    for index, values in raw.items():
        spec = specs[index]
        kind = spec[2]
        last = values[-1]
        converted: ConfigValue
        if kind == "profile":
            profile = last
            continue
        if kind == "config_path":
            config_path = last
            continue
        if kind in flags:
            flags[kind] = True
            continue
        if kind == "flag":
            converted = ConfigValue_Boolean(value=True)
        elif kind == "array":
            converted = ConfigValue_Array(values=CottList(values=[ConfigValue_Text(value=v) for v in values]))
        elif kind == "int":
            try:
                number = int(last)
            except ValueError:
                return _usage(f"Invalid value for {_names(spec)}: '{last}' is not a valid integer.")
            if number < -1:
                return _usage(f"Invalid value for {_names(spec)}: {number} is not in the range x>=-1.")
            converted = ConfigValue_Integer(value=number)
        elif kind == "float":
            try:
                real = float(last)
            except ValueError:
                return _usage(f"Invalid value for {_names(spec)}: '{last}' is not a valid float.")
            if not real > 0:
                return _usage(f"Invalid value for {_names(spec)}: {real} is not in the range x>0.")
            converted = ConfigValue_Real(value=real)
        elif kind == "adapter" or kind == "choice":
            match = [c for c in spec[3] if c.casefold() == last.casefold()]
            if not match:
                choices = ", ".join(f"'{c}'" for c in spec[3])
                return _usage(f"Invalid value for {_names(spec)}: '{last}' is not one of {choices}.")
            converted = ConfigValue_Text(value=match[0].lower() if kind == "adapter" else match[0])
        else:
            converted = ConfigValue_Text(value=last)
        explicit.append(ConfigEntry(key=spec[1], value=converted))
    return Ok(value=CliArguments(
        conn_str=CottList(values=conn_str),
        profile=Some(value=profile) if profile is not None else Nothing(),
        config_path=Some(value=config_path) if config_path is not None else Nothing(),
        explicit=CottList(values=explicit),
        run_config_wizard=flags["wizard"],
        run_keys_app=flags["keys"],
        show_version=flags["version"],
        show_help=flags["help"],
    ))
