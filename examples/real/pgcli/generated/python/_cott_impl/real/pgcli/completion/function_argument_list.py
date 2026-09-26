import re

from cott_runtime import CottList, Some

from real.pgcli.completion_types import ArgumentListUsage, ArgumentListUsage_Call, ArgumentListUsage_CallDisplay, FunctionMetadata
from real.pgcli.parseutils import parse_function_defaults


def function_argument_list(function: FunctionMetadata, usage: ArgumentListUsage, casing: CottList[str]) -> str:
    case_map: dict[str, str] = {c.lower(): c for c in casing}
    names: list[str] = [str(x) for x in function.arg_names.value] if isinstance(function.arg_names, Some) else []
    all_modes: list[str] = [str(x) for x in function.arg_modes.value] if isinstance(function.arg_modes, Some) else []
    arg_types: list[str] = [str(x) for x in function.arg_types.value] if isinstance(function.arg_types, Some) else []
    kept: list[tuple[str, str]] = []
    if names:
        modes = all_modes if all_modes else ["i"] * len(names)
        types = arg_types if arg_types else ["None"] * len(names)
        for name, typ, mode in zip(names, types, modes):
            if mode in ("i", "b", "v"):
                kept.append((name, typ))
    n = len(kept)
    defaults_text = function.arg_defaults.value if isinstance(function.arg_defaults, Some) else ""
    defaults = [str(x) for x in parse_function_defaults(defaults_text)]
    d = len(defaults)

    if isinstance(usage, ArgumentListUsage_Call):
        if n < 2 or "v" in all_modes:
            return "()"
        multiline = n > 2
        width = max(len(name) for name, _ in kept) if multiline else 0
        parts: list[str] = []
        for k, (name, _typ) in enumerate(kept):
            default = ""
            if k + d >= n:
                default = re.sub(r"::[\w\.]+(\[\])?$", "", defaults[k - n + d])
            cased = case_map.get(name, name)
            if multiline:
                cased = cased.ljust(width)
            text = cased + " := " + default
            if text:
                parts.append(text)
        if multiline:
            return "(" + ",".join("\n    " + p for p in parts) + "\n)"
        return "(" + ", ".join(parts) + ")"
    if isinstance(usage, ArgumentListUsage_CallDisplay):
        items = [case_map.get(name, name) for name, _ in kept]
    else:
        items = [case_map.get(name, name) + " " + typ for name, typ in kept]
    return "(" + ", ".join(i for i in items if i) + ")"
