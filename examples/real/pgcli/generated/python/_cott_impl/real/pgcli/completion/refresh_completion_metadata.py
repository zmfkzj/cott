import io
import os
from pathlib import Path
from typing import cast

import psycopg
from cott_runtime import CottContractViolation, Err, Ok, Opaque, Result, Some, _cott_fixture_database, _cott_fixture_read, _cott_fixture_write
from real.pgcli.completion_types import CASING_QUERY, COLUMNS_QUERY, COLUMNS_QUERY_LEGACY, DATABASES_QUERY, DATATYPES_QUERY, DATATYPES_QUERY_LEGACY, FOREIGN_KEYS_QUERY, FUNCTIONS_QUERY_LEGACY, FUNCTIONS_QUERY_V11, FUNCTIONS_QUERY_V84, FUNCTIONS_QUERY_V9, RELATIONS_QUERY, SCHEMATA_QUERY, SEARCH_PATH_FALLBACK_QUERY, SEARCH_PATH_QUERY, CompletionCatalog, MetadataRefreshError, MetadataRefreshError_CasingFileFailed, MetadataRefreshError_QueryFailed, MetadataRefreshError_VirtualDatabase, MetadataRefreshRequest
from real.pgcli.connection_types import Executor


def _rows(conn: psycopg.Connection[tuple[object, ...]], query: str, params: list[object] | None) -> list[tuple[object, ...]]:
    with conn.cursor() as cur:
        cur.execute(query.encode("utf-8"), params)
        return cur.fetchall()


def _array(value: object) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return cast(list[str], value)
    if isinstance(value, tuple):
        return list(cast(tuple[str, ...], value))
    raise psycopg.ProgrammingError("Catalog array has an unexpected type")


def _search_path(conn: psycopg.Connection[tuple[object, ...]]) -> list[str]:
    try:
        return [cast(str, row[0]) for row in _rows(conn, SEARCH_PATH_QUERY, None)]
    except psycopg.ProgrammingError:
        with conn.cursor() as cur:
            cur.execute(SEARCH_PATH_FALLBACK_QUERY.encode("utf-8"))
            row = cur.fetchone()
        if row is None:
            raise psycopg.ProgrammingError("Search path fallback did not return a schema list")
        schemas = _array(row[0])
        if schemas is None:
            raise psycopg.ProgrammingError("Search path fallback did not return a schema list")
        return schemas


def _relations(conn: psycopg.Connection[tuple[object, ...]], kinds: list[str], version: int) -> list[tuple[str, str, list[tuple[str, str, bool, str | None]]]]:
    params: list[object] = [kinds]
    relations: list[tuple[str, str, list[tuple[str, str, bool, str | None]]]] = []
    positions: dict[tuple[str, str], int] = {}
    for row in _rows(conn, RELATIONS_QUERY, params):
        key = cast(str, row[0]), cast(str, row[1])
        positions[key] = len(relations)
        relations.append((key[0], key[1], []))
    query = COLUMNS_QUERY if version >= 80400 else COLUMNS_QUERY_LEGACY
    for row in _rows(conn, query, params):
        key = cast(str, row[0]), cast(str, row[1])
        if key not in positions:
            positions[key] = len(relations)
            relations.append((key[0], key[1], []))
        relations[positions[key]][2].append((cast(str, row[2]), cast(str, row[3]), row[4] is True, cast(str | None, row[5])))
    return relations


def _fixture_read(path: Path) -> tuple[bool, bytes | None]:
    try:
        return True, _cott_fixture_read(path)
    except CottContractViolation as error:
        if error.message == "fixture adapters are inactive":
            return False, None
        cause = error.__cause__
        if isinstance(cause, (FileNotFoundError, NotADirectoryError, IsADirectoryError)):
            return True, None
        if isinstance(cause, OSError):
            raise cause
        raise


def _fixture_write(path: Path, data: bytes) -> bool:
    try:
        _cott_fixture_write(path, data)
        return True
    except CottContractViolation as error:
        if error.message == "fixture adapters are inactive":
            return False
        cause = error.__cause__
        if isinstance(cause, OSError):
            raise cause
        raise


def _casing(conn: psycopg.Connection[tuple[object, ...]], path: Path, generate: bool) -> list[str]:
    active, contents = _fixture_read(path)
    if active:
        if contents is None and generate:
            words = [cast(str, row[0]) for row in _rows(conn, CASING_QUERY, None)]
            _fixture_write(path, "\n".join(words).encode("utf-8"))
            _, contents = _fixture_read(path)
        if contents is None:
            return []
        with io.TextIOWrapper(io.BytesIO(contents), encoding="utf-8") as handle:
            return [line.strip() for line in handle]
    if generate and not os.path.isfile(path):
        words = [cast(str, row[0]) for row in _rows(conn, CASING_QUERY, None)]
        text = "\n".join(words)
        if not _fixture_write(path, text.encode("utf-8")):
            with open(path, "w") as handle:
                handle.write(text)
    if os.path.isfile(path):
        with open(path) as handle:
            return [line.strip() for line in handle]
    return []


def refresh_completion_metadata(executor: Executor, request: MetadataRefreshRequest) -> Result[CompletionCatalog, MetadataRefreshError]:
    if executor.virtual_database:
        return Err[MetadataRefreshError](error=MetadataRefreshError_VirtualDatabase())
    try:
        try:
            _cott_fixture_database("read")
        except CottContractViolation as error:
            if error.message != "fixture adapters are inactive":
                raise
        conn = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
        version = conn.info.server_version
        search_path = _search_path(conn)
        schemata = [cast(str, row[0]) for row in _rows(conn, SCHEMATA_QUERY, None)]
        tables = _relations(conn, ["r", "p", "f"], version)
        foreign_keys: list[tuple[str, str, str, str, str, str]] = []
        if version >= 90000:
            for row in _rows(conn, FOREIGN_KEYS_QUERY, None):
                foreign_keys.append((cast(str, row[0]), cast(str, row[1]), cast(str, row[2]), cast(str, row[3]), cast(str, row[4]), cast(str, row[5])))
        views = _relations(conn, ["v", "m"], version)
        datatypes_query = DATATYPES_QUERY if version > 90000 else DATATYPES_QUERY_LEGACY
        datatypes = [(cast(str, row[0]), cast(str, row[1])) for row in _rows(conn, datatypes_query, None)]
        databases = [cast(str, row[0]) for row in _rows(conn, DATABASES_QUERY, None)]
        casing: list[str] = []
        if isinstance(request.casing_file, Some):
            path = request.casing_file.value
            try:
                casing = _casing(conn, path, request.generate_casing_file)
            except OSError as error:
                return Err[MetadataRefreshError](error=MetadataRefreshError_CasingFileFailed(path=path, message=str(error)))
        if version >= 110000:
            functions_query = FUNCTIONS_QUERY_V11
        elif version > 90000:
            functions_query = FUNCTIONS_QUERY_V9
        elif version >= 80400:
            functions_query = FUNCTIONS_QUERY_V84
        else:
            functions_query = FUNCTIONS_QUERY_LEGACY
        functions: list[tuple[str, str, list[str] | None, list[str] | None, list[str] | None, str, bool, bool, bool, bool, str | None]] = []
        for row in _rows(conn, functions_query, None):
            functions.append((cast(str, row[0]), cast(str, row[1]), _array(row[2]), _array(row[3]), _array(row[4]), cast(str, row[5]).strip(), row[6] is True, row[7] is True, row[8] is True, row[9] is True, cast(str | None, row[10])))
    except (psycopg.Error, OSError) as error:
        return Err[MetadataRefreshError](error=MetadataRefreshError_QueryFailed(message=str(error)))
    data: dict[str, object] = {
        "schemata": schemata,
        "tables": tables,
        "views": views,
        "functions": functions,
        "datatypes": datatypes,
        "foreign_keys": foreign_keys,
        "databases": databases,
        "search_path": search_path,
        "casing": casing,
    }
    return Ok(value=Opaque(tag="pgcli.completion-catalog", value=data))
