import re
from typing import cast

import psycopg
import sqlparse
from cott_runtime import UNIT, CottList, Err, Ok, Result, Unit

from real.pgcli.connection_types import Executor
from real.pgcli.session_types import EvaluateError, EvaluateError_Failed


def _statements(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    comments: list[str] = []
    while True:
        match = re.match(r"^(/\*.*?\*/|--.*?)(?:\n|$)", text, re.DOTALL)
        if match is None:
            break
        comments.append(match.group(0))
        text = text[match.end():].lstrip()
    pieces: list[str] = sqlparse.split(text)
    if comments and pieces:
        pieces[0] = "".join(comments) + pieces[0]
    elif comments:
        pieces = ["".join(comments)]
    statements: list[str] = []
    for piece in pieces:
        sql = sqlparse.format(piece, strip_comments=True).strip().rstrip(";").strip()
        if sql:
            statements.append(sql)
    return statements


def run_init_commands(executor: Executor, commands: CottList[str]) -> Result[Unit, EvaluateError]:
    try:
        connection = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
        for command in commands:
            for sql in _statements(command):
                with connection.cursor() as cursor:
                    cursor.execute(sql.encode("utf-8"))
    except Exception as error:
        return Err[EvaluateError](error=EvaluateError_Failed(message=str(error)))
    return Ok(value=UNIT)
