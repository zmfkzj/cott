from cott_runtime import CottList, Err, Ok, Result
from real.harlequin.core_types import SqlClientError, SqlClientError_EmptySql, SqlClientError_UnterminatedSql


def split_statements(sql: str) -> Result[CottList[str], SqlClientError]:
    statements: list[str] = []
    start = 0
    i = 0
    n = len(sql)
    has_code = False
    while i < n:
        ch = sql[i]
        if ch in ("'", '"', "`"):
            has_code = True
            j = i + 1
            while True:
                if j >= n:
                    return Err(error=SqlClientError_UnterminatedSql(delimiter=ch))
                if sql[j] == ch:
                    if j + 1 < n and sql[j + 1] == ch:
                        j += 2
                        continue
                    break
                j += 1
            i = j + 1
        elif ch == "-" and sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j < 0 else j + 1
        elif ch == "/" and sql.startswith("/*", i):
            j = sql.find("*/", i + 2)
            if j < 0:
                return Err(error=SqlClientError_UnterminatedSql(delimiter="*/"))
            i = j + 2
        elif ch == ";":
            stmt = sql[start:i].strip()
            if has_code:
                statements.append(stmt)
            i += 1
            start = i
            has_code = False
        else:
            if not ch.isspace():
                has_code = True
            i += 1
    tail = sql[start:].strip()
    if has_code:
        statements.append(tail)
    if not statements:
        return Err(error=SqlClientError_EmptySql())
    return Ok(value=CottList(values=statements))
