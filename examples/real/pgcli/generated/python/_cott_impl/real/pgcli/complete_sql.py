from cott_runtime import CottList
from real.pgcli_types import CompletionRequest, CompletionResult, TableCatalog


def _identifier_character(character: str) -> bool:
    return character.isalnum() or character == "_" or character == "$"


def _replacement(source: str, cursor: int) -> tuple[int, str]:
    start = cursor
    while start > 0 and _identifier_character(source[start - 1]):
        start -= 1
    return start, source[start:cursor]


def _tokenize(source: str) -> list[str]:
    tokens: list[str] = []
    index = 0
    length = len(source)
    while index < length:
        character = source[index]
        if character.isspace():
            index += 1
        elif character == "-" and index + 1 < length and source[index + 1] == "-":
            index += 2
            while index < length and source[index] != "\n":
                index += 1
        elif character == "/" and index + 1 < length and source[index + 1] == "*":
            index += 2
            while index + 1 < length and not (source[index] == "*" and source[index + 1] == "/"):
                index += 1
            if index + 1 < length:
                index += 2
        elif character == "'":
            index += 1
            while index < length:
                if source[index] != "'":
                    index += 1
                elif index + 1 < length and source[index + 1] == "'":
                    index += 2
                else:
                    index += 1
                    break
        elif character == '"':
            index += 1
            quoted = ""
            while index < length:
                if source[index] != '"':
                    quoted += source[index]
                    index += 1
                elif index + 1 < length and source[index + 1] == '"':
                    quoted += '"'
                    index += 2
                else:
                    index += 1
                    break
            if quoted != "":
                tokens.append(quoted)
        elif _identifier_character(character):
            end = index + 1
            while end < length and _identifier_character(source[end]):
                end += 1
            tokens.append(source[index:end])
            index = end
        else:
            tokens.append(character)
            index += 1
    return tokens


def _identifier_token(token: str) -> bool:
    if token == "":
        return False
    for character in token:
        if not _identifier_character(character):
            return False
    return True


def _alias_token(token: str) -> bool:
    if not _identifier_token(token):
        return False
    return token.casefold() not in (
        "as",
        "cross",
        "except",
        "fetch",
        "for",
        "full",
        "group",
        "having",
        "inner",
        "intersect",
        "join",
        "left",
        "limit",
        "offset",
        "on",
        "order",
        "outer",
        "returning",
        "right",
        "set",
        "union",
        "values",
        "where",
        "window",
    )


def _parse_reference(tokens: list[str], start: int) -> tuple[tuple[str, str, str] | None, int]:
    if start >= len(tokens) or not _identifier_token(tokens[start]):
        return None, start
    schema = ""
    name = tokens[start]
    index = start + 1
    if index + 1 < len(tokens) and tokens[index] == "." and _identifier_token(tokens[index + 1]):
        schema = name
        name = tokens[index + 1]
        index += 2
    alias = name
    if index + 1 < len(tokens) and tokens[index].casefold() == "as" and _alias_token(tokens[index + 1]):
        alias = tokens[index + 1]
        index += 2
    elif index < len(tokens) and _alias_token(tokens[index]):
        alias = tokens[index]
        index += 1
    return (schema, name, alias), index


def _table_references(tokens: list[str]) -> list[tuple[str, str, str]]:
    references: list[tuple[str, str, str]] = []
    index = 0
    in_from = False
    while index < len(tokens):
        token = tokens[index].casefold()
        parse_at = -1
        if token == "from":
            in_from = True
            parse_at = index + 1
        elif token == "join":
            parse_at = index + 1
        elif token == "update" or token == "into":
            in_from = False
            parse_at = index + 1
        elif token in ("except", "group", "having", "intersect", "limit", "offset", "order", "returning", "set", "union", "values", "where", "window"):
            in_from = False
        elif token == "," and in_from:
            parse_at = index + 1
        if parse_at >= 0:
            reference, next_index = _parse_reference(tokens, parse_at)
            if reference is not None:
                references.append(reference)
                index = next_index
                continue
        index += 1
    return references


def _expects_table(tokens: list[str]) -> bool:
    if len(tokens) == 0:
        return False
    last = tokens[-1].casefold()
    if last in ("from", "into", "join", "table", "update"):
        return True
    if last != ",":
        return False
    index = len(tokens) - 2
    while index >= 0:
        token = tokens[index].casefold()
        if token in ("from", "join"):
            return True
        if token in ("except", "group", "having", "intersect", "limit", "offset", "order", "returning", "select", "set", "union", "values", "where", "window"):
            return False
        index -= 1
    return False


def _reference_matches(schema: str, name: str, references: list[tuple[str, str, str]]) -> bool:
    folded_schema = schema.casefold()
    folded_name = name.casefold()
    for reference_schema, reference_name, _ in references:
        if reference_name.casefold() == folded_name and (reference_schema == "" or reference_schema.casefold() == folded_schema):
            return True
    return False


def _qualifier_matches(schema: str, name: str, qualifier: str, previous: str, references: list[tuple[str, str, str]]) -> bool:
    folded_schema = schema.casefold()
    folded_name = name.casefold()
    folded_qualifier = qualifier.casefold()
    if previous != "":
        return folded_schema == previous.casefold() and folded_name == folded_qualifier
    for reference_schema, reference_name, reference_alias in references:
        if reference_alias.casefold() != folded_qualifier and reference_name.casefold() != folded_qualifier:
            continue
        if reference_name.casefold() == folded_name and (reference_schema == "" or reference_schema.casefold() == folded_schema):
            return True
    return len(references) == 0 and folded_name == folded_qualifier


def _append_candidate(candidates: list[str], seen: set[str], candidate: str, alternate: str, prefix: str) -> None:
    folded_prefix = prefix.casefold()
    if not candidate.casefold().startswith(folded_prefix) and not alternate.casefold().startswith(folded_prefix):
        return
    key = candidate.casefold()
    if key not in seen:
        seen.add(key)
        candidates.append(candidate)


def _catalog_candidates(catalog: CottList[TableCatalog], context_tokens: list[str], query_tokens: list[str], prefix: str) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()
    references = _table_references(query_tokens)
    qualifier = ""
    previous = ""
    table_context_tokens = context_tokens
    if len(context_tokens) >= 2 and context_tokens[-1] == ".":
        qualifier = context_tokens[-2]
        table_context_tokens = context_tokens[:-2]
        if len(context_tokens) >= 4 and context_tokens[-3] == ".":
            previous = context_tokens[-4]
            table_context_tokens = context_tokens[:-4]
    table_context = _expects_table(table_context_tokens)
    if table_context:
        for table in catalog:
            if qualifier != "" and (previous != "" or table.schema.casefold() != qualifier.casefold()):
                continue
            if qualifier == "":
                candidate = table.name if table.schema == "" else table.schema + "." + table.name
            else:
                candidate = table.name
            _append_candidate(candidates, seen, candidate, table.name, prefix)
        return candidates
    if qualifier != "":
        matched_table = False
        for table in catalog:
            if _qualifier_matches(table.schema, table.name, qualifier, previous, references):
                matched_table = True
                for column in table.columns:
                    _append_candidate(candidates, seen, column.name, column.name, prefix)
        if matched_table:
            return candidates
        if previous == "":
            for table in catalog:
                if table.schema.casefold() == qualifier.casefold():
                    _append_candidate(candidates, seen, table.name, table.name, prefix)
        return candidates
    for table in catalog:
        if len(references) == 0 or _reference_matches(table.schema, table.name, references):
            for column in table.columns:
                _append_candidate(candidates, seen, column.name, column.name, prefix)
    return candidates


def complete_sql(request: CompletionRequest) -> CompletionResult:
    source = request.source
    cursor = request.cursor
    if cursor > len(source):
        cursor = len(source)
    replace_start, prefix = _replacement(source, cursor)
    context_tokens = _tokenize(source[:replace_start])
    query_tokens = list(context_tokens)
    query_tokens.extend(_tokenize(source[cursor:]))
    candidates = _catalog_candidates(request.catalog, context_tokens, query_tokens, prefix)
    result_candidates: CottList[str] = CottList(values=tuple(candidates))
    return CompletionResult(candidates=result_candidates, replace_start=replace_start)
