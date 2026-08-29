from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from declarations.core_types import ByteBlock, LABEL_BYTES, LabelFrame, NonEmptyLabel

def package_label(label: NonEmptyLabel, values: CottArray[U8, Literal[4]], raw: CottBuffer[Literal[4]]) -> tuple[str, LabelFrame[CottArray[U8, Literal[4]]], ByteBlock[Literal[4]]]:
    """Return a named fixed-width label, its covariant array-payload frame, and matching raw bytes."""
    label = _cott_validate_abi(label, NonEmptyLabel, path="$.label")
    values = _cott_validate_abi(values, CottArray[U8, Literal[4]], path="$.values")
    raw = _cott_validate_abi(raw, CottBuffer[Literal[4]], path="$.raw")
    if not ((len(values) == LABEL_BYTES)):
        raise CottContractViolation("requires clause failed", symbol="declarations.presentation.package_label", clause="requires:1", phase="requires", span={"end_byte":421,"end_column":39,"end_line":14,"start_byte":387,"start_column":5,"start_line":14}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/declarations/presentation/package_label.py", "54bfa42801042ad46f3e96d0ce2c209dcf7de4797bbee0c0a3ac00045f28ee92", "package_label", expected_project_name="declarations-generics", expected_cott_symbol="declarations.presentation.package_label")
        _result = _implementation(label, values, raw)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "declarations.presentation.package_label"
        if _error.span is None:
            _error.span = {"end_byte":438,"end_column":1,"end_line":17,"start_byte":116,"start_column":1,"start_line":5}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="declarations.presentation.package_label", phase="implementation-call", span={"end_byte":438,"end_column":1,"end_line":17,"start_byte":116,"start_column":1,"start_line":5}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="declarations.presentation.package_label", phase="implementation-call", span={"end_byte":438,"end_column":1,"end_line":17,"start_byte":116,"start_column":1,"start_line":5}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, tuple[str, LabelFrame[CottArray[U8, Literal[4]]], ByteBlock[Literal[4]]], path="$.return")
    _result = _cott_wrap_async_protocol(_result, tuple[str, LabelFrame[CottArray[U8, Literal[4]]], ByteBlock[Literal[4]]], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["package_label"]
