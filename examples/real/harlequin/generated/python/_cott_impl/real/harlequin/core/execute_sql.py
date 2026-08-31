import sqlite3

from cott_runtime import CottList, Err, Ok, Result
from real.harlequin.core_types import (
    Cell,
    Cell_Blob,
    Cell_Integer,
    Cell_Null,
    Cell_Real,
    Cell_Text,
    DatabaseTarget,
    DatabaseTarget_File,
    DatabaseTarget_Memory,
    QueryResult,
    SqlClientError,
    SqlClientError_EmptySql,
    SqlClientError_ReadOnlyViolation,
    SqlClientError_UnsupportedValue,
    SqlClientError_UnterminatedSql,
    TypedRow,
)


def _split_sql(sql: str) -> tuple[list[str], str | None]:
    statements: list[str] = []
    buffer: list[str] = []
    state = "normal"
    has_code = False
    index = 0
    while index < len(sql):
        character = sql[index]
        following = sql[index + 1] if index + 1 < len(sql) else ""
        if state == "normal":
            if character == "-" and following == "-":
                buffer.append(character)
                buffer.append(following)
                state = "line-comment"
                index += 2
                continue
            if character == "/" and following == "*":
                buffer.append(character)
                buffer.append(following)
                state = "block-comment"
                index += 2
                continue
            if character == "'":
                buffer.append(character)
                state = "single-quote"
                has_code = True
                index += 1
                continue
            if character == '"':
                buffer.append(character)
                state = "double-quote"
                has_code = True
                index += 1
                continue
            if character == "`":
                buffer.append(character)
                state = "backtick"
                has_code = True
                index += 1
                continue
            if character == "[":
                buffer.append(character)
                state = "bracket"
                has_code = True
                index += 1
                continue
            if character == ";":
                if has_code:
                    candidate = "".join(buffer)
                    if not sqlite3.complete_statement(candidate + character):
                        buffer.append(character)
                        index += 1
                        continue
                    statements.append(candidate.strip())
                buffer = []
                has_code = False
                index += 1
                continue
            buffer.append(character)
            if not character.isspace():
                has_code = True
            index += 1
            continue
        if state == "line-comment":
            buffer.append(character)
            if character == "\n":
                state = "normal"
            index += 1
            continue
        if state == "block-comment":
            buffer.append(character)
            if character == "*" and following == "/":
                buffer.append(following)
                state = "normal"
                index += 2
            else:
                index += 1
            continue
        buffer.append(character)
        if state == "single-quote" and character == "'":
            if following == "'":
                buffer.append(following)
                index += 2
            else:
                state = "normal"
                index += 1
            continue
        if state == "double-quote" and character == '"':
            if following == '"':
                buffer.append(following)
                index += 2
            else:
                state = "normal"
                index += 1
            continue
        if state == "backtick" and character == "`":
            if following == "`":
                buffer.append(following)
                index += 2
            else:
                state = "normal"
                index += 1
            continue
        if state == "bracket" and character == "]":
            if following == "]":
                buffer.append(following)
                index += 2
            else:
                state = "normal"
                index += 1
            continue
        index += 1

    if state == "single-quote":
        return statements, "'"
    if state == "double-quote":
        return statements, '"'
    if state == "backtick":
        return statements, "`"
    if state == "bracket":
        return statements, "["
    if state == "block-comment":
        return statements, "/*"
    if has_code:
        statements.append("".join(buffer).strip())
    return statements, None


def _statement_is_read_only(statement: str) -> bool:
    keywords: list[str] = []
    state = "normal"
    depth = 0
    has_top_level_assignment = False
    index = 0
    while index < len(statement):
        character = statement[index]
        following = statement[index + 1] if index + 1 < len(statement) else ""
        if state == "normal":
            if character == "-" and following == "-":
                state = "line-comment"
                index += 2
                continue
            if character == "/" and following == "*":
                state = "block-comment"
                index += 2
                continue
            if character == "'":
                state = "single-quote"
                index += 1
                continue
            if character == '"':
                state = "double-quote"
                index += 1
                continue
            if character == "`":
                state = "backtick"
                index += 1
                continue
            if character == "[":
                state = "bracket"
                index += 1
                continue
            if character == "(":
                depth += 1
                index += 1
                continue
            if character == ")":
                if depth > 0:
                    depth -= 1
                index += 1
                continue
            if depth == 0 and character == "=":
                has_top_level_assignment = True
                index += 1
                continue
            if depth == 0 and (character.isalpha() or character == "_"):
                end = index + 1
                while end < len(statement) and (statement[end].isalnum() or statement[end] == "_"):
                    end += 1
                keywords.append(statement[index:end].upper())
                index = end
                continue
            index += 1
            continue
        if state == "line-comment":
            if character == "\n":
                state = "normal"
            index += 1
            continue
        if state == "block-comment":
            if character == "*" and following == "/":
                state = "normal"
                index += 2
            else:
                index += 1
            continue
        if state == "single-quote" and character == "'":
            if following == "'":
                index += 2
            else:
                state = "normal"
                index += 1
            continue
        if state == "double-quote" and character == '"':
            if following == '"':
                index += 2
            else:
                state = "normal"
                index += 1
            continue
        if state == "backtick" and character == "`":
            if following == "`":
                index += 2
            else:
                state = "normal"
                index += 1
            continue
        if state == "bracket" and character == "]":
            if following == "]":
                index += 2
            else:
                state = "normal"
                index += 1
            continue
        index += 1

    if len(keywords) == 0:
        return False
    first = keywords[0]
    if first == "SELECT" or first == "VALUES" or first == "EXPLAIN":
        return True
    if first == "PRAGMA":
        return not has_top_level_assignment
    if first != "WITH":
        return False
    for keyword in keywords[1:]:
        if keyword == "SELECT" or keyword == "VALUES":
            return True
        if keyword == "INSERT" or keyword == "UPDATE" or keyword == "DELETE" or keyword == "REPLACE":
            return False
    return False


def _to_cell(value: object) -> Cell | None:
    match value:
        case None:
            return Cell_Null()
        case bool() as integer_value:
            return Cell_Integer(value=integer_value)
        case int() as integer_value:
            return Cell_Integer(value=integer_value)
        case float() as real_value:
            return Cell_Real(value=real_value)
        case str() as text_value:
            return Cell_Text(value=text_value)
        case bytes() as blob_value:
            return Cell_Blob(value=blob_value)
        case _:
            return None


def execute_sql(database: DatabaseTarget, sql: str, read_only: bool) -> Result[CottList[QueryResult], SqlClientError]:
    statements, unterminated_delimiter = _split_sql(sql)
    if unterminated_delimiter is not None:
        return Err(error=SqlClientError_UnterminatedSql(delimiter=unterminated_delimiter))
    if len(statements) == 0:
        return Err(error=SqlClientError_EmptySql())
    if read_only:
        for statement in statements:
            if not _statement_is_read_only(statement):
                return Err(error=SqlClientError_ReadOnlyViolation(statement=statement))

    match database:
        case DatabaseTarget_Memory():
            connection = sqlite3.connect(":memory:")
        case DatabaseTarget_File(path=path):
            connection = sqlite3.connect(path)
    if read_only:
        connection.execute("PRAGMA query_only = ON")

    results: list[QueryResult] = []
    for statement in statements:
        cursor = connection.execute(statement)
        columns: list[str] = []
        rows: list[TypedRow] = []
        if cursor.description is not None:
            columns = [description[0] for description in cursor.description]
            for raw_row in cursor.fetchall():
                values: list[Cell] = []
                for raw_value in raw_row:
                    cell = _to_cell(raw_value)
                    if cell is None:
                        connection.close()
                        return Err(error=SqlClientError_UnsupportedValue(type_name="unsupported SQLite value"))
                    values.append(cell)
                rows.append(TypedRow(values=CottList(values=values)))
        affected_rows = cursor.rowcount
        if affected_rows < 0:
            affected_rows = 0
        results.append(
            QueryResult(
                columns=CottList(values=columns),
                rows=CottList(values=rows),
                affected_rows=affected_rows,
            )
        )

    connection.commit()
    connection.close()
    return Ok(value=CottList(values=results))
