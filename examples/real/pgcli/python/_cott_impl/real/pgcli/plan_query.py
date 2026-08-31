from cott_runtime import Err, Ok, Result
from real.pgcli_types import ClientError, ClientError_InvalidSql, InputBuffer, QueryPlan


def _dollar_delimiter_end(source: str, start: int) -> int:
    index = start + 1
    if index < len(source) and source[index] == "$":
        return index + 1
    if index >= len(source) or not (source[index] == "_" or source[index].isalpha()):
        return -1
    index += 1
    while index < len(source) and (source[index] == "_" or source[index].isalnum()):
        index += 1
    if index < len(source) and source[index] == "$":
        return index + 1
    return -1


def _scan_query(source: str) -> tuple[int, bool, str]:
    statement_count = 0
    statement_has_content = False
    index = 0
    while index < len(source):
        character = source[index]
        if character.isspace():
            index += 1
        elif character == "-" and index + 1 < len(source) and source[index + 1] == "-":
            newline = source.find("\n", index + 2)
            if newline < 0:
                index = len(source)
            else:
                index = newline + 1
        elif character == "/" and index + 1 < len(source) and source[index + 1] == "*":
            depth = 1
            index += 2
            while index < len(source) and depth > 0:
                if index + 1 < len(source) and source[index] == "/" and source[index + 1] == "*":
                    depth += 1
                    index += 2
                elif index + 1 < len(source) and source[index] == "*" and source[index + 1] == "/":
                    depth -= 1
                    index += 2
                else:
                    index += 1
            if depth != 0:
                return (statement_count, statement_has_content, "unterminated block comment")
        elif character == "'":
            statement_has_content = True
            index += 1
            closed = False
            while index < len(source):
                if source[index] == "'":
                    if index + 1 < len(source) and source[index + 1] == "'":
                        index += 2
                    else:
                        index += 1
                        closed = True
                        break
                elif source[index] == "\\" and index + 1 < len(source):
                    index += 2
                else:
                    index += 1
            if not closed:
                return (statement_count, statement_has_content, "unterminated string literal")
        elif character == '"':
            statement_has_content = True
            index += 1
            closed = False
            while index < len(source):
                if source[index] == '"':
                    if index + 1 < len(source) and source[index + 1] == '"':
                        index += 2
                    else:
                        index += 1
                        closed = True
                        break
                else:
                    index += 1
            if not closed:
                return (statement_count, statement_has_content, "unterminated quoted identifier")
        elif character == "$":
            delimiter_end = _dollar_delimiter_end(source, index)
            if delimiter_end < 0:
                statement_has_content = True
                index += 1
            else:
                statement_has_content = True
                delimiter = source[index:delimiter_end]
                close = source.find(delimiter, delimiter_end)
                if close < 0:
                    return (statement_count, statement_has_content, "unterminated dollar-quoted string")
                index = close + len(delimiter)
        elif character == ";":
            if statement_has_content:
                statement_count += 1
                statement_has_content = False
            index += 1
        else:
            statement_has_content = True
            index += 1
    if statement_has_content:
        statement_count += 1
    return (statement_count, statement_has_content, "")


def plan_query(buffer: InputBuffer) -> Result[QueryPlan, ClientError]:
    statement_count, unterminated_statement, scan_error = _scan_query(buffer.text)
    if scan_error != "":
        return Err(error=ClientError_InvalidSql(message=scan_error))
    if statement_count == 0:
        return Err(error=ClientError_InvalidSql(message="query is empty"))
    return Ok(
        value=QueryPlan(
            sql=buffer.text,
            statement_count=statement_count,
            requires_terminator=buffer.multiline and unterminated_statement,
        )
    )
