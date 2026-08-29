from cott_runtime import CottList, Err, Ok, Result
from real.harlequin.core_types import SqlClientError, SqlClientError_EmptySql, SqlClientError_UnterminatedSql


def split_statements(sql: str) -> Result[CottList[str], SqlClientError]:
    statements: list[str] = []
    current: list[str] = []
    delimiter = ""
    contains_sql = False
    index = 0

    while index < len(sql):
        character = sql[index]
        following = sql[index + 1] if index + 1 < len(sql) else ""

        if delimiter == "--":
            current.append(character)
            if character == "\n" or character == "\r":
                delimiter = ""
            index += 1
        elif delimiter == "/*":
            current.append(character)
            if character == "*" and following == "/":
                current.append(following)
                delimiter = ""
                index += 2
            else:
                index += 1
        elif delimiter == "'":
            current.append(character)
            if character == "'":
                if following == "'":
                    current.append(following)
                    index += 2
                else:
                    delimiter = ""
                    index += 1
            else:
                index += 1
        elif delimiter == '"':
            current.append(character)
            if character == '"':
                if following == '"':
                    current.append(following)
                    index += 2
                else:
                    delimiter = ""
                    index += 1
            else:
                index += 1
        elif delimiter == "`":
            current.append(character)
            if character == "`":
                if following == "`":
                    current.append(following)
                    index += 2
                else:
                    delimiter = ""
                    index += 1
            else:
                index += 1
        elif delimiter == "[":
            current.append(character)
            if character == "]":
                delimiter = ""
            index += 1
        elif character == "-" and following == "-":
            current.append(character)
            current.append(following)
            delimiter = "--"
            index += 2
        elif character == "/" and following == "*":
            current.append(character)
            current.append(following)
            delimiter = "/*"
            index += 2
        elif character == "'" or character == '"' or character == "`" or character == "[":
            current.append(character)
            delimiter = character
            contains_sql = True
            index += 1
        elif character == ";":
            if contains_sql:
                statements.append("".join(current).strip())
            current = []
            contains_sql = False
            index += 1
        else:
            current.append(character)
            if not character.isspace():
                contains_sql = True
            index += 1

    if delimiter != "" and delimiter != "--":
        return Err(error=SqlClientError_UnterminatedSql(delimiter=delimiter))
    if contains_sql:
        statements.append("".join(current).strip())
    if len(statements) == 0:
        return Err(error=SqlClientError_EmptySql())
    return Ok(value=CottList(values=tuple(statements)))
