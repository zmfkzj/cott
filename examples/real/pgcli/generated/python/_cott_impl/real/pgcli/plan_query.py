from cott_runtime import Err, Ok, Result
from real.pgcli_types import ClientError, ClientError_InvalidSql, InputBuffer, QueryPlan


def _invalid(message: str) -> Result[QueryPlan, ClientError]:
    return Err(error=ClientError_InvalidSql(message=message))


def _is_ident_start(ch: str) -> bool:
    return ch.isalpha() or ch == "_" or ord(ch) >= 128


def _is_ident_char(ch: str) -> bool:
    return _is_ident_start(ch) or ch.isdigit() or ch == "$"


def plan_query(buffer: InputBuffer) -> Result[QueryPlan, ClientError]:
    text = buffer.text
    n = len(text)
    i = 0
    count = 0
    has_content = False
    terminated = False
    unclosed = False

    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue

        if ch == "-" and i + 1 < n and text[i + 1] == "-":
            end = text.find("\n", i + 2)
            if end < 0:
                i = n
            else:
                i = end + 1
            continue

        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            depth = 1
            i += 2
            while i < n and depth > 0:
                if text.startswith("/*", i):
                    depth += 1
                    i += 2
                elif text.startswith("*/", i):
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth > 0:
                unclosed = True
            continue

        if ch == ";":
            if has_content:
                count += 1
            has_content = False
            terminated = True
            i += 1
            continue

        has_content = True
        terminated = False

        if ch == "'" or ch == '"':
            i += 1
            closed = False
            while i < n:
                if text[i] == ch:
                    if i + 1 < n and text[i + 1] == ch:
                        i += 2
                        continue
                    i += 1
                    closed = True
                    break
                i += 1
            if not closed:
                unclosed = True
            continue

        if ch == "$" and (i == 0 or not _is_ident_char(text[i - 1])):
            j = i + 1
            if j < n and _is_ident_start(text[j]):
                j += 1
                while j < n and (_is_ident_start(text[j]) or text[j].isdigit()):
                    j += 1
            if j < n and text[j] == "$":
                tag = text[i : j + 1]
                end = text.find(tag, j + 1)
                if end < 0:
                    unclosed = True
                    i = n
                else:
                    i = end + len(tag)
                continue

        if _is_ident_char(ch):
            i += 1
            while i < n and _is_ident_char(text[i]):
                i += 1
            continue

        i += 1

    if has_content:
        count += 1

    if count == 0:
        return _invalid("no SQL statement")

    if unclosed and not buffer.multiline:
        return _invalid("unterminated quote or comment")

    requires = buffer.multiline and (unclosed or not terminated)
    return Ok(value=QueryPlan(sql=text, statement_count=count, requires_terminator=requires))
