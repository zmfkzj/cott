import json
import re
from typing import cast

from real.pgcli.completion_types import PGLITERALS_JSON


def _upper_words(literals: dict[object, object], key: str) -> set[str]:
    raw = literals.get(key)
    if not isinstance(raw, list):
        return set()
    return {w for w in cast(list[object], raw) if isinstance(w, str)}


def escape_identifier_name(name: str) -> str:
    if not name:
        return name
    parsed = cast(object, json.loads(PGLITERALS_JSON))
    literals: dict[object, object] = cast(dict[object, object], parsed) if isinstance(parsed, dict) else {}
    upper = name.upper()
    if (
        not re.match(r"^[_a-z][_a-z0-9\$]*$", name)
        or upper in _upper_words(literals, "reserved")
        or upper in _upper_words(literals, "functions")
    ):
        return '"' + name + '"'
    return name
