from real.pgcli_types import HighlightedSql, HighlightRequest


def _is_identifier_start(character: str) -> bool:
    return character == "_" or character.isalpha()


def _is_identifier_continue(character: str) -> bool:
    return character == "_" or character == "$" or character.isalnum()


def _is_keyword(value: str) -> bool:
    return value.casefold() in (
        "abort",
        "all",
        "alter",
        "analyse",
        "analyze",
        "and",
        "any",
        "array",
        "as",
        "asc",
        "asymmetric",
        "authorization",
        "begin",
        "between",
        "bigint",
        "binary",
        "bit",
        "boolean",
        "both",
        "by",
        "case",
        "cast",
        "char",
        "character",
        "check",
        "coalesce",
        "collate",
        "column",
        "commit",
        "concurrently",
        "constraint",
        "create",
        "cross",
        "current_catalog",
        "current_date",
        "current_role",
        "current_schema",
        "current_time",
        "current_timestamp",
        "current_user",
        "database",
        "dec",
        "decimal",
        "default",
        "deferrable",
        "delete",
        "desc",
        "distinct",
        "do",
        "double",
        "drop",
        "else",
        "end",
        "except",
        "exists",
        "explain",
        "false",
        "fetch",
        "filter",
        "float",
        "for",
        "foreign",
        "freeze",
        "from",
        "full",
        "grant",
        "group",
        "having",
        "ilike",
        "in",
        "initially",
        "inner",
        "insert",
        "int",
        "integer",
        "intersect",
        "interval",
        "into",
        "is",
        "isnull",
        "join",
        "json",
        "json_array",
        "json_object",
        "lateral",
        "leading",
        "left",
        "like",
        "limit",
        "localtime",
        "localtimestamp",
        "lock",
        "natural",
        "nchar",
        "new",
        "no",
        "none",
        "normalize",
        "not",
        "notnull",
        "null",
        "nullif",
        "numeric",
        "offset",
        "old",
        "on",
        "only",
        "or",
        "order",
        "outer",
        "over",
        "overlaps",
        "placing",
        "position",
        "precision",
        "primary",
        "procedure",
        "real",
        "references",
        "returning",
        "right",
        "rollback",
        "row",
        "rows",
        "select",
        "session_user",
        "set",
        "similar",
        "smallint",
        "some",
        "symmetric",
        "table",
        "tablesample",
        "then",
        "time",
        "timestamp",
        "to",
        "trailing",
        "transaction",
        "treat",
        "trigger",
        "trim",
        "true",
        "truncate",
        "union",
        "unique",
        "unknown",
        "update",
        "user",
        "using",
        "values",
        "varchar",
        "variadic",
        "verbose",
        "view",
        "when",
        "where",
        "window",
        "with",
        "xml",
    )


def _scan_single_quoted(source: str, start: int) -> int:
    index = start + 1
    while index < len(source):
        if source[index] == "'":
            if index + 1 < len(source) and source[index + 1] == "'":
                index += 2
            else:
                return index + 1
        elif source[index] == "\\" and index + 1 < len(source):
            index += 2
        else:
            index += 1
    return -1


def _scan_quoted_identifier(source: str, start: int) -> int:
    index = start + 1
    while index < len(source):
        if source[index] == '"':
            if index + 1 < len(source) and source[index + 1] == '"':
                index += 2
            else:
                return index + 1
        else:
            index += 1
    return -1


def _scan_block_comment(source: str, start: int) -> int:
    index = start + 2
    depth = 1
    while index < len(source):
        if index + 1 < len(source) and source[index] == "/" and source[index + 1] == "*":
            depth += 1
            index += 2
        elif index + 1 < len(source) and source[index] == "*" and source[index + 1] == "/":
            depth -= 1
            index += 2
            if depth == 0:
                return index
        else:
            index += 1
    return -1


def _dollar_delimiter_end(source: str, start: int) -> int:
    index = start + 1
    if index < len(source) and source[index] == "$":
        return index + 1
    if index >= len(source) or not _is_identifier_start(source[index]):
        return -1
    index += 1
    while index < len(source) and (source[index] == "_" or source[index].isalnum()):
        index += 1
    if index < len(source) and source[index] == "$":
        return index + 1
    return -1


def _scan_number(source: str, start: int) -> int:
    index = start
    if source[index] == ".":
        index += 1
        while index < len(source) and source[index].isdigit():
            index += 1
        return index
    if index + 2 <= len(source) and source[index] == "0" and index + 1 < len(source):
        marker = source[index + 1].casefold()
        if marker == "x":
            index += 2
            while index < len(source) and (source[index].isdigit() or "a" <= source[index].casefold() <= "f" or source[index] == "_"):
                index += 1
            return index
        if marker == "b" or marker == "o":
            index += 2
            while index < len(source) and (source[index].isdigit() or source[index] == "_"):
                index += 1
            return index
    while index < len(source) and (source[index].isdigit() or source[index] == "_"):
        index += 1
    if index < len(source) and source[index] == "." and (index + 1 >= len(source) or source[index + 1] != "."):
        index += 1
        while index < len(source) and (source[index].isdigit() or source[index] == "_"):
            index += 1
    if index < len(source) and source[index].casefold() == "e":
        exponent = index + 1
        if exponent < len(source) and (source[exponent] == "+" or source[exponent] == "-"):
            exponent += 1
        digit = exponent
        while exponent < len(source) and (source[exponent].isdigit() or source[exponent] == "_"):
            exponent += 1
        if exponent > digit:
            index = exponent
    return index


def _append_colored(parts: list[str], value: str, code: str, enabled: bool) -> None:
    if enabled:
        parts.append(code)
        parts.append(value)
        parts.append("\x1b[0m")
    else:
        parts.append(value)


def highlight_sql(request: HighlightRequest) -> HighlightedSql:
    source = request.source
    parts: list[str] = []
    contains_error = False
    index = 0
    while index < len(source):
        character = source[index]
        if character == "-" and index + 1 < len(source) and source[index + 1] == "-":
            end = source.find("\n", index + 2)
            if end < 0:
                end = len(source)
            _append_colored(parts, source[index:end], "\x1b[90m", request.color)
            index = end
        elif character == "/" and index + 1 < len(source) and source[index + 1] == "*":
            end = _scan_block_comment(source, index)
            if end < 0:
                contains_error = True
                _append_colored(parts, source[index:], "\x1b[1;31m", request.color)
                index = len(source)
            else:
                _append_colored(parts, source[index:end], "\x1b[90m", request.color)
                index = end
        elif character == "'":
            end = _scan_single_quoted(source, index)
            if end < 0:
                contains_error = True
                _append_colored(parts, source[index:], "\x1b[1;31m", request.color)
                index = len(source)
            else:
                _append_colored(parts, source[index:end], "\x1b[32m", request.color)
                index = end
        elif character == '"':
            end = _scan_quoted_identifier(source, index)
            if end < 0:
                contains_error = True
                _append_colored(parts, source[index:], "\x1b[1;31m", request.color)
                index = len(source)
            else:
                _append_colored(parts, source[index:end], "\x1b[33m", request.color)
                index = end
        elif character == "$":
            delimiter_end = _dollar_delimiter_end(source, index)
            if delimiter_end < 0:
                parts.append(character)
                index += 1
            else:
                delimiter = source[index:delimiter_end]
                close = source.find(delimiter, delimiter_end)
                if close < 0:
                    contains_error = True
                    _append_colored(parts, source[index:], "\x1b[1;31m", request.color)
                    index = len(source)
                else:
                    end = close + len(delimiter)
                    _append_colored(parts, source[index:end], "\x1b[32m", request.color)
                    index = end
        elif character.isdigit() or (character == "." and index + 1 < len(source) and source[index + 1].isdigit()):
            end = _scan_number(source, index)
            _append_colored(parts, source[index:end], "\x1b[35m", request.color)
            index = end
        elif _is_identifier_start(character):
            end = index + 1
            while end < len(source) and _is_identifier_continue(source[end]):
                end += 1
            value = source[index:end]
            if _is_keyword(value):
                _append_colored(parts, value, "\x1b[1;36m", request.color)
            else:
                parts.append(value)
            index = end
        else:
            parts.append(character)
            index += 1
    return HighlightedSql(text="".join(parts), contains_error=contains_error)
