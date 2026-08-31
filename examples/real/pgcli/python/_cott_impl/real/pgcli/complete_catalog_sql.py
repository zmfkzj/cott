from cott_runtime import CottList
from real.pgcli_types import CompletionPolicy, CompletionRequest, CompletionResult


def _is_identifier_character(character: str) -> bool:
    return character == "_" or character == "$" or character.isalnum()


def _identifier_start(source: str, end: int) -> int:
    start = end
    while start > 0 and _is_identifier_character(source[start - 1]):
        start -= 1
    return start


def _qualified_start(source: str, fragment_start: int) -> int:
    start = fragment_start
    while start > 0 and source[start - 1] == ".":
        part_end = start - 1
        part_start = _identifier_start(source, part_end)
        if part_start == part_end:
            break
        start = part_start
    return start


def _previous_word(source: str, end: int) -> str:
    index = end
    while index > 0 and source[index - 1].isspace():
        index -= 1
    word_start = _identifier_start(source, index)
    return source[word_start:index].casefold()


def _is_relation_context(source: str, compound_start: int) -> bool:
    previous = _previous_word(source, compound_start)
    return previous == "from" or previous == "join" or previous == "update" or previous == "into" or previous == "table"


def _append_candidate(candidates: list[str], seen: set[str], candidate: str, prefix: str) -> None:
    folded = candidate.casefold()
    if folded.startswith(prefix) and folded not in seen:
        seen.add(folded)
        candidates.append(candidate)


def _candidate_sort_key(candidate: str) -> tuple[str, str]:
    return (candidate.casefold(), candidate)


def _sort_candidates(candidates: list[str]) -> None:
    decorated: list[tuple[tuple[str, str], str]] = []
    for candidate in candidates:
        decorated.append((_candidate_sort_key(candidate), candidate))
    decorated.sort()
    index = 0
    while index < len(decorated):
        candidates[index] = decorated[index][1]
        index += 1


def _append_keywords(candidates: list[str], seen: set[str], prefix: str) -> None:
    keywords = (
        "ALL",
        "ALTER",
        "AND",
        "AS",
        "ASC",
        "BEGIN",
        "BY",
        "CASE",
        "COMMIT",
        "CREATE",
        "DELETE",
        "DESC",
        "DISTINCT",
        "DROP",
        "ELSE",
        "END",
        "EXISTS",
        "FALSE",
        "FROM",
        "FULL",
        "GROUP",
        "HAVING",
        "IN",
        "INDEX",
        "INNER",
        "INSERT",
        "INTO",
        "IS",
        "JOIN",
        "LEFT",
        "LIKE",
        "LIMIT",
        "NOT",
        "NULL",
        "OFFSET",
        "ON",
        "OR",
        "ORDER",
        "OUTER",
        "RETURNING",
        "RIGHT",
        "ROLLBACK",
        "SELECT",
        "SET",
        "TABLE",
        "THEN",
        "TRUE",
        "UNION",
        "UPDATE",
        "VALUES",
        "VIEW",
        "WHEN",
        "WHERE",
        "WITH",
    )
    for keyword in keywords:
        _append_candidate(candidates, seen, keyword, prefix)


def _append_unqualified_catalog(candidates: list[str], seen: set[str], prefix: str, request: CompletionRequest, relation_context: bool) -> None:
    for table in request.catalog:
        _append_candidate(candidates, seen, table.name, prefix)
        if table.schema != "":
            _append_candidate(candidates, seen, table.schema + "." + table.name, prefix)
        if not relation_context:
            for column in table.columns:
                _append_candidate(candidates, seen, column.name, prefix)


def _append_qualified_catalog(candidates: list[str], seen: set[str], prefix: str, qualifier: str, request: CompletionRequest, relation_context: bool) -> None:
    folded_qualifier = qualifier.casefold()
    separator = folded_qualifier.rfind(".")
    if separator >= 0:
        schema = folded_qualifier[:separator]
        table_name = folded_qualifier[separator + 1 :]
        for table in request.catalog:
            if table.schema.casefold() == schema and table.name.casefold() == table_name:
                for column in table.columns:
                    _append_candidate(candidates, seen, column.name, prefix)
        return

    matched_table = False
    if not relation_context:
        for table in request.catalog:
            if table.name.casefold() == folded_qualifier:
                matched_table = True
                for column in table.columns:
                    _append_candidate(candidates, seen, column.name, prefix)
    if relation_context or not matched_table:
        for table in request.catalog:
            if table.schema.casefold() == folded_qualifier:
                _append_candidate(candidates, seen, table.name, prefix)


def complete_catalog_sql(request: CompletionRequest, policy: CompletionPolicy) -> CompletionResult:
    cursor = request.cursor
    source_length = len(request.source)
    if cursor > source_length:
        cursor = source_length

    fragment_start = _identifier_start(request.source, cursor)
    compound_start = _qualified_start(request.source, fragment_start)
    prefix = request.source[fragment_start:cursor].casefold()
    relation_context = _is_relation_context(request.source, compound_start)
    candidates: list[str] = []
    seen: set[str] = set()

    if compound_start < fragment_start:
        qualifier = request.source[compound_start : fragment_start - 1]
        _append_qualified_catalog(candidates, seen, prefix, qualifier, request, relation_context)
    else:
        _append_unqualified_catalog(candidates, seen, prefix, request, relation_context)
        if policy.include_keywords:
            _append_keywords(candidates, seen, prefix)

    _sort_candidates(candidates)
    if len(candidates) > policy.max_candidates:
        candidates = candidates[: policy.max_candidates]
    return CompletionResult(candidates=CottList(values=candidates), replace_start=fragment_start)
