import re

from cott_runtime import CottList, Some
from real.pgcli.completion_types import ArgumentListUsage, ArgumentListUsage_Call, ArgumentListUsage_CallDisplay, FunctionMetadata
from real.pgcli.parseutils import parse_function_defaults


def function_argument_list(function: FunctionMetadata, usage: ArgumentListUsage, casing: CottList[str]) -> str:
    case_map = {word.lower(): word for word in casing}
    names = list(function.arg_names.value) if isinstance(function.arg_names, Some) else []
    modes = list(function.arg_modes.value) if isinstance(function.arg_modes, Some) else []
    types = list(function.arg_types.value) if isinstance(function.arg_types, Some) else []
    kept = [(name, typ) for name, typ, mode in zip(names, types or ["None"] * len(names), modes or ["i"] * len(names)) if mode in ("i", "b", "v")]
    count = len(kept)
    if isinstance(usage, ArgumentListUsage_Call):
        if count < 2 or "v" in modes:
            return "()"
        defaults_text = function.arg_defaults.value if isinstance(function.arg_defaults, Some) else ""
        defaults = parse_function_defaults(defaults_text)
        default_count = len(defaults)
        multiline = count > 2
        width = max(len(name) for name, _ in kept) if multiline else 0
        parts: list[str] = []
        for index, (name, _typ) in enumerate(kept):
            default = re.sub(r"::[\w\.]+(\[\])?$", "", defaults[index - count + default_count]) if index + default_count >= count else ""
            cased = case_map.get(name, name)
            parts.append((cased.ljust(width) if multiline else cased) + " := " + default)
        if multiline:
            return "(" + ",".join("\n    " + part for part in parts) + "\n)"
        return "(" + ", ".join(parts) + ")"
    if isinstance(usage, ArgumentListUsage_CallDisplay):
        return "(" + ", ".join(case_map.get(name, name) for name, _ in kept) + ")"
    return "(" + ", ".join(case_map.get(name, name) + " " + typ for name, typ in kept) + ")"
