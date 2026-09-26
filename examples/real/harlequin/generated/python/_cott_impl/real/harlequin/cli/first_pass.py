from cott_runtime import CottList, Nothing, Option, Some

from real.harlequin.cli_types import FirstPass


def _opt(value: str | None) -> Option[str]:
    if value is None:
        return Nothing()
    return Some(value=value)


def first_pass(arguments: CottList[str]) -> FirstPass:
    args: list[str] = [a for a in arguments]
    values: dict[str, str] = {}
    flags: set[str] = set()
    i = 0
    n = len(args)
    while i < n:
        arg = args[i]
        if arg == "--":
            break
        key: str | None = None
        value: str | None = None
        consumed_next = False
        if arg in ("-a", "--adapter"):
            key = "adapter"
            consumed_next = True
        elif arg in ("-P", "--profile"):
            key = "profile"
            consumed_next = True
        elif arg == "--config-path":
            key = "config_path"
            consumed_next = True
        elif arg.startswith("--adapter="):
            key, value = "adapter", arg[len("--adapter="):]
        elif arg.startswith("--profile="):
            key, value = "profile", arg[len("--profile="):]
        elif arg.startswith("--config-path="):
            key, value = "config_path", arg[len("--config-path="):]
        elif arg.startswith("-a") and not arg.startswith("--"):
            key, value = "adapter", arg[2:]
        elif arg.startswith("-P") and not arg.startswith("--"):
            key, value = "profile", arg[2:]
        elif arg in ("--help", "--version", "--config", "--keys"):
            flags.add(arg)
        if consumed_next:
            if i + 1 < n:
                value = args[i + 1]
                i += 1
            else:
                key = None
        if key is not None and value is not None:
            values[key] = value.lower() if key == "adapter" else value
        i += 1
    return FirstPass(
        adapter=_opt(values.get("adapter")),
        profile=_opt(values.get("profile")),
        config_path=_opt(values.get("config_path")),
        wants_help="--help" in flags,
        wants_version="--version" in flags,
        wants_config_wizard="--config" in flags,
        wants_keys_app="--keys" in flags,
    )
