from typing import cast

from real.pgcli.completion_types import CompletionCatalog


def apply_identifier_casing(catalog: CompletionCatalog, word: str) -> str:
    data = cast(dict[str, object], catalog.unwrap())
    casing = cast(list[str], data["casing"])
    mapping: dict[str, str] = {w.lower(): w for w in casing}
    return mapping.get(word, word)
