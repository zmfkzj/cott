from cott_runtime import CottList, Err, Ok, Result, U32
from real.harlequin.core_types import (
    Connection,
    QueryBatch,
    QueryResult,
    SqlClientError,
    SqlClientError_EmptySql,
    SqlClientError_ReadOnlyViolation,
    SqlClientError_ResultLimitExceeded,
    SqlClientError_UnterminatedSql,
    TypedRow,
)


def execute_statements(connection: Connection, sql: str, maximum_rows: U32) -> Result[QueryBatch, SqlClientError]:
    statements: list[str] = []
    statement_start = 0
    statement_has_code = False
    index = 0
    delimiter = ""
    dollar_delimiter = False
    line_comment = False
    block_comment_depth = 0

    while index < len(sql):
        character = sql[index]
        next_character = sql[index + 1] if index + 1 < len(sql) else ""

        if line_comment:
            if character == "\n" or character == "\r":
                line_comment = False
            index += 1
            continue

        if block_comment_depth > 0:
            if character == "/" and next_character == "*":
                block_comment_depth += 1
                index += 2
            elif character == "*" and next_character == "/":
                block_comment_depth -= 1
                index += 2
            else:
                index += 1
            continue

        if delimiter != "":
            if dollar_delimiter:
                if sql.startswith(delimiter, index):
                    index += len(delimiter)
                    delimiter = ""
                    dollar_delimiter = False
                else:
                    index += 1
                continue

            if character == "\\" and index + 1 < len(sql):
                index += 2
                continue
            if character == delimiter:
                if next_character == delimiter:
                    index += 2
                else:
                    delimiter = ""
                    index += 1
                continue
            index += 1
            continue

        if character == "-" and next_character == "-":
            line_comment = True
            index += 2
            continue
        if character == "/" and next_character == "*":
            block_comment_depth = 1
            index += 2
            continue
        if character == "'" or character == '"' or character == "`":
            delimiter = character
            statement_has_code = True
            index += 1
            continue
        if character == "[":
            delimiter = "]"
            statement_has_code = True
            index += 1
            continue
        if character == "$":
            delimiter_end = index + 1
            while delimiter_end < len(sql) and (sql[delimiter_end].isalnum() or sql[delimiter_end] == "_"):
                delimiter_end += 1
            if delimiter_end < len(sql) and sql[delimiter_end] == "$":
                delimiter = sql[index : delimiter_end + 1]
                dollar_delimiter = True
                statement_has_code = True
                index = delimiter_end + 1
                continue
        if character == ";":
            if statement_has_code:
                statements.append(sql[statement_start:index].strip())
            statement_start = index + 1
            statement_has_code = False
            index += 1
            continue
        if not character.isspace():
            statement_has_code = True
        index += 1

    if delimiter != "":
        return Err(error=SqlClientError_UnterminatedSql(delimiter=delimiter))
    if block_comment_depth > 0:
        return Err(error=SqlClientError_UnterminatedSql(delimiter="*/"))
    if statement_has_code:
        statements.append(sql[statement_start:].strip())
    if len(statements) == 0:
        return Err(error=SqlClientError_EmptySql())

    results: list[QueryResult] = []
    for statement in statements:
        executable = statement.lstrip()
        while executable.startswith("--") or executable.startswith("/*"):
            if executable.startswith("--"):
                comment_end = executable.find("\n")
                if comment_end < 0:
                    executable = ""
                    break
                executable = executable[comment_end + 1 :].lstrip()
            else:
                comment_end = executable.find("*/", 2)
                if comment_end < 0:
                    executable = ""
                    break
                executable = executable[comment_end + 2 :].lstrip()

        keyword_end = 0
        while keyword_end < len(executable) and (executable[keyword_end].isalpha() or executable[keyword_end] == "_"):
            keyword_end += 1
        keyword = executable[:keyword_end].casefold()
        if connection.read_only and keyword not in ("select", "with", "values", "show", "describe", "desc", "explain", "pragma"):
            return Err(error=SqlClientError_ReadOnlyViolation(statement=statement))

        columns: CottList[str] = CottList(values=[])
        rows: CottList[TypedRow] = CottList(values=[])
        result = QueryResult(columns=columns, rows=rows, affected_rows=0)
        if len(result.rows) > maximum_rows:
            return Err(error=SqlClientError_ResultLimitExceeded(limit=maximum_rows))
        results.append(result)

    return Ok(value=QueryBatch(statements=CottList(values=statements), results=CottList(values=results)))
