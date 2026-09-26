import os
from pathlib import Path
from typing import cast

import psycopg
from cott_runtime import Err, Ok, Opaque, Result, Some

from real.pgcli.completion_types import (
    CASING_QUERY,
    COLUMNS_QUERY,
    COLUMNS_QUERY_LEGACY,
    DATABASES_QUERY,
    DATATYPES_QUERY,
    DATATYPES_QUERY_LEGACY,
    FOREIGN_KEYS_QUERY,
    FUNCTIONS_QUERY_LEGACY,
    FUNCTIONS_QUERY_V11,
    FUNCTIONS_QUERY_V84,
    FUNCTIONS_QUERY_V9,
    RELATIONS_QUERY,
    SCHEMATA_QUERY,
    SEARCH_PATH_FALLBACK_QUERY,
    SEARCH_PATH_QUERY,
    CompletionCatalog,
    MetadataRefreshError,
    MetadataRefreshError_CasingFileFailed,
    MetadataRefreshError_QueryFailed,
    MetadataRefreshError_VirtualDatabase,
    MetadataRefreshRequest,
)
from real.pgcli.connection_types import Executor


def _rows(conn: psycopg.Connection[tuple[object, ...]], query: str, params: list[object] | None) -> list[tuple[object, ...]]:
    with conn.cursor() as cur:
        _ = cur.execute(query.encode("utf-8"), params)
        return list(cur.fetchall())


def _string_array(value: object) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return [str(item) for item in cast(list[object], value)]
    if isinstance(value, tuple):
        return [str(item) for item in cast(tuple[object, ...], value)]
    raise psycopg.ProgrammingError("Catalog array has an unexpected type")


def _optional_string(value: object) -> str | None:
    return None if value is None else str(value)


def _relations(conn: psycopg.Connection[tuple[object, ...]], kinds: list[str], version: int) -> list[tuple[str, str, list[tuple[str, str, bool, str | None]]]]:
    params: list[object] = [kinds]
    relations: list[tuple[str, str, list[tuple[str, str, bool, str | None]]]] = []
    positions: dict[tuple[str, str], int] = {}
    for row in _rows(conn, RELATIONS_QUERY, params):
        key = (str(row[0]), str(row[1]))
        positions[key] = len(relations)
        relations.append((key[0], key[1], []))
    query = COLUMNS_QUERY if version >= 80400 else COLUMNS_QUERY_LEGACY
    for row in _rows(conn, query, params):
        key = (str(row[0]), str(row[1]))
        if key not in positions:
            positions[key] = len(relations)
            relations.append((key[0], key[1], []))
        relations[positions[key]][2].append((str(row[2]), str(row[3]), row[4] is True, _optional_string(row[5])))
    return relations


def _casing(conn: psycopg.Connection[tuple[object, ...]], path: Path, generate: bool) -> list[str]:
    if generate and not os.path.isfile(path):
        words = [str(row[0]) for row in _rows(conn, CASING_QUERY, None)]
        with open(path, "w") as handle:
            _ = handle.write("\n".join(words))
    if os.path.isfile(path):
        with open(path) as handle:
            return [line.strip() for line in handle]
    return []


def refresh_completion_metadata(executor: Executor, request: MetadataRefreshRequest) -> Result[CompletionCatalog, MetadataRefreshError]:
    if executor.virtual_database:
        return Err(error=MetadataRefreshError_VirtualDatabase())
    conn = cast(psycopg.Connection[tuple[object, ...]], executor.connection.unwrap())
    try:
        version = conn.info.server_version
        try:
            search_path = [str(row[0]) for row in _rows(conn, SEARCH_PATH_QUERY, None)]
        except psycopg.ProgrammingError:
            with conn.cursor() as cur:
                _ = cur.execute(SEARCH_PATH_FALLBACK_QUERY.encode("utf-8"))
                first = cur.fetchone()
            if first is None:
                raise psycopg.ProgrammingError("Search path fallback did not return a schema list")
            search_path = _string_array(first[0]) or []
        schemata = [str(row[0]) for row in _rows(conn, SCHEMATA_QUERY, None)]
        tables = _relations(conn, ["r", "p", "f"], version)
        foreign_keys: list[tuple[str, str, str, str, str, str]] = []
        if version >= 90000:
            for row in _rows(conn, FOREIGN_KEYS_QUERY, None):
                foreign_keys.append((str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), str(row[5])))
        views = _relations(conn, ["v", "m"], version)
        datatypes_query = DATATYPES_QUERY if version > 90000 else DATATYPES_QUERY_LEGACY
        datatypes = [(str(row[0]), str(row[1])) for row in _rows(conn, datatypes_query, None)]
        databases = [str(row[0]) for row in _rows(conn, DATABASES_QUERY, None)]
        casing: list[str] = []
        if isinstance(request.casing_file, Some):
            path = request.casing_file.value
            try:
                casing = _casing(conn, path, request.generate_casing_file)
            except OSError as error:
                return Err(error=MetadataRefreshError_CasingFileFailed(path=path, message=str(error)))
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
            functions.append((str(row[0]), str(row[1]), _string_array(row[2]), _string_array(row[3]), _string_array(row[4]), str(row[5] if row[5] is not None else "").strip(), row[6] is True, row[7] is True, row[8] is True, row[9] is True, _optional_string(row[10])))
    except psycopg.Error as error:
        return Err(error=MetadataRefreshError_QueryFailed(message=str(error)))
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
