from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.json_to_csv_types import CsvRecord

def escape_csv_field(field: str) -> str:
    """Escape one field for a comma-separated record.

Fields containing a comma, double quote, carriage return, or line feed are
enclosed in double quotes. Each double quote inside a quoted field is
doubled. All other characters, including Unicode characters, are copied
unchanged."""
    field = _cott_validate_abi(field, str, path="$.field")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/json_to_csv/escape_csv_field.py", "021e9d22c2140622f9b81da5b762b229e5a31b236289d37f1ffa49c1a0b36990", "escape_csv_field", expected_project_name="json-to-csv", expected_cott_symbol="curriculum.json_to_csv.escape_csv_field")
        _result = _implementation(field)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.json_to_csv.escape_csv_field"
        if _error.span is None:
            _error.span = {"end_byte":457,"end_column":1,"end_line":18,"start_byte":96,"start_column":1,"start_line":8}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.json_to_csv.escape_csv_field", phase="implementation-call", span={"end_byte":457,"end_column":1,"end_line":18,"start_byte":96,"start_column":1,"start_line":8}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.json_to_csv.escape_csv_field", phase="implementation-call", span={"end_byte":457,"end_column":1,"end_line":18,"start_byte":96,"start_column":1,"start_line":8}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def serialize_csv(rows: CottList[CsvRecord]) -> str:
    """Serialize typed records as comma-separated values.

The output begins with the literal header `name,age,birthyear`. Records
follow in input order, with fields in name, age, birthyear order. Each field
is serialized by `escape_csv_field`.

Every record ends with CRLF (`\\r\\n`), including the last record. Empty
input therefore returns exactly `name,age,birthyear\\r\\n`."""
    rows = _cott_validate_abi(rows, CottList[CsvRecord], path="$.rows")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/json_to_csv/serialize_csv.py", "ce9fc2da0aa9f91a6b602e6e0addd1818aa1977fb7b18187921686f9c817e527", "serialize_csv", expected_project_name="json-to-csv", expected_cott_symbol="curriculum.json_to_csv.serialize_csv")
        _result = _implementation(rows)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.json_to_csv.serialize_csv"
        if _error.span is None:
            _error.span = {"end_byte":955,"end_column":1,"end_line":31,"start_byte":457,"start_column":1,"start_line":18}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.json_to_csv.serialize_csv", phase="implementation-call", span={"end_byte":955,"end_column":1,"end_line":31,"start_byte":457,"start_column":1,"start_line":18}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.json_to_csv.serialize_csv", phase="implementation-call", span={"end_byte":955,"end_column":1,"end_line":31,"start_byte":457,"start_column":1,"start_line":18}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) >= 20)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.json_to_csv.serialize_csv", clause="ensures:1", phase="ensures", span={"end_byte":954,"end_column":29,"end_line":30,"start_byte":930,"start_column":5,"start_line":30}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["CsvRecord", "escape_csv_field", "serialize_csv"]
