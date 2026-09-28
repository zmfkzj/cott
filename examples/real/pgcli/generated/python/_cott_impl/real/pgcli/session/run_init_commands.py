import re
from typing import cast

import psycopg
import sqlparse
from cott_runtime import CottContractViolation, CottList, Err, Ok, Result, UNIT, Unit, _cott_fixture_database

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
        raw_connection = executor.connection.unwrap()
        if not isinstance(raw_connection, psycopg.Connection):
            raise TypeError("executor connection must be a psycopg connection")
        connection = cast(psycopg.Connection[tuple[object, ...]], raw_connection)
        boundary_pending = True
        for command in commands:
            for sql in _statements(command):
                with connection.cursor() as cursor:
                    if boundary_pending:
                        try:
                            _cott_fixture_database("read")
                        except CottContractViolation as error:
                            if error.message != "fixture adapters are inactive":
                                raise
                        boundary_pending = False
                    cursor.execute(sql.encode("utf-8"))
    except Exception as error:
        return Err[EvaluateError](error=EvaluateError_Failed(message=str(error)))
    return Ok(value=UNIT)
