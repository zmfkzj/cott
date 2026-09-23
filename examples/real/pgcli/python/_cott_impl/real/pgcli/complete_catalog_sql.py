from typing import Final

from cott_runtime import CottList
from real.pgcli_types import CompletionPolicy, CompletionRequest, CompletionResult

_KEYWORDS: Final[str] = "SELECT FROM WHERE JOIN LEFT RIGHT INNER OUTER ON GROUP BY ORDER HAVING LIMIT OFFSET INSERT INTO VALUES UPDATE SET DELETE AND OR NOT NULL AS DISTINCT"
_TABLE_CONTEXT: Final[str] = "FROM JOIN INTO UPDATE TABLE"


def _is_word_char(ch: str) -> bool:
    return ch.isalnum() or ch == "_" or ch == "."


def complete_catalog_sql(request: CompletionRequest, policy: CompletionPolicy) -> CompletionResult:
    source = request.source
    cursor = min(int(request.cursor), len(source))
    start = cursor
    while start > 0 and _is_word_char(source[start - 1]):
        start -= 1
    prefix = source[start:cursor].lower()
    previous_words = source[:start].split()
    previous = previous_words[-1].upper() if previous_words else ""
    tables_only = previous in _TABLE_CONTEXT.split()

    pool: list[str] = []
    for table in request.catalog:
        pool.append(table.name)
        pool.append(table.schema + "." + table.name)
        if not tables_only:
            for column in table.columns:
                pool.append(column.name)
    if policy.include_keywords and not tables_only:
        pool.extend(_KEYWORDS.split())

    seen: set[str] = set()
    matches: list[str] = []
    for candidate in pool:
        if candidate and candidate not in seen and candidate.lower().startswith(prefix):
            seen.add(candidate)
            matches.append(candidate)
    matches.sort(key=lambda c: (c.lower(), c))
    limit = int(policy.max_candidates)
    return CompletionResult(candidates=CottList(values=matches[:limit]), replace_start=start)
