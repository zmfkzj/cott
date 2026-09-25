import unicodedata
from typing import Final

from cott_runtime import CottList
from real.pgcli_types import SQL_KEYWORDS, CompletionPolicy, CompletionRequest, CompletionResult

_ASCII_UPPER: Final[str] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_ASCII_LOWER: Final[str] = "abcdefghijklmnopqrstuvwxyz"
_RELATION_WORDS: Final[str] = "from join into update table"


def _ascii_lower(text: str) -> str:
    return text.translate(str.maketrans(_ASCII_UPPER, _ASCII_LOWER))


def _is_word_char(ch: str) -> bool:
    return ch.isalpha() or unicodedata.category(ch) == "Nd" or ch == "_" or ch == "."


def complete_catalog_sql(request: CompletionRequest, policy: CompletionPolicy) -> CompletionResult:
    source = request.source
    cursor = request.cursor
    start = cursor
    while start > 0 and _is_word_char(source[start - 1]):
        start -= 1
    prefix = _ascii_lower(source[start:cursor])
    previous_words = source[:start].split()
    relation = len(previous_words) > 0 and _ascii_lower(previous_words[-1]) in _RELATION_WORDS.split()

    pool: list[str] = []
    for table in request.catalog:
        pool.append(table.name)
        pool.append(table.schema + "." + table.name)
        if not relation:
            for column in table.columns:
                pool.append(column.name)
    if policy.include_keywords and not relation:
        pool.extend(SQL_KEYWORDS.split())

    seen: set[str] = set()
    keyed: list[tuple[str, str]] = []
    for candidate in pool:
        lowered = _ascii_lower(candidate)
        if candidate not in seen and lowered.startswith(prefix):
            seen.add(candidate)
            keyed.append((lowered, candidate))
    keyed.sort()
    matches = [candidate for _, candidate in keyed[: policy.max_candidates]]
    return CompletionResult(candidates=CottList(values=matches), replace_start=start)
