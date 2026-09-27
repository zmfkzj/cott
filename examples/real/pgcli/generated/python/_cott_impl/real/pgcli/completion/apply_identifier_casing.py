from typing import cast

from real.pgcli.completion_types import CompletionCatalog


def apply_identifier_casing(catalog: CompletionCatalog, word: str) -> str:
    payload = catalog.unwrap()
    if not isinstance(payload, dict):
        raise TypeError("completion catalog must contain a dictionary")
    data = cast(dict[str, object], payload)
    casing = data["casing"]
    if not isinstance(casing, list):
        raise TypeError("completion catalog casing must be a list")
    mapping: dict[str, str] = {}
    for entry in cast(list[object], casing):
        if not isinstance(entry, str):
            raise TypeError("completion catalog casing entries must be strings")
        mapping[entry.lower()] = entry
    return mapping.get(word, word)
