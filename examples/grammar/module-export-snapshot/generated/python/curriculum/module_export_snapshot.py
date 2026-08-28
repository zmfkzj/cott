from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.module_export_snapshot_types import ModuleSnapshot

def build_snapshot(exported_x: I64, module_x: I64) -> ModuleSnapshot:
    """Construct a module snapshot without transforming or cross-assigning either
input. `exported_x` is assigned to `exported_x`, and `module_x` is assigned
independently to `module_x`. The construction is deterministic and accepts
every I64 value, including both bounds and equal input values."""
    exported_x = _cott_validate_abi(exported_x, I64, path="$.exported_x")
    module_x = _cott_validate_abi(module_x, I64, path="$.module_x")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/module_export_snapshot/build_snapshot.py", "5df1876f4d5469159d1db8826f77fbe9cd03f759552805d1b58c26bbdf1403a3", "build_snapshot", expected_project_name="module-export-snapshot", expected_cott_symbol="curriculum.module_export_snapshot.build_snapshot")
        _result = _implementation(exported_x, module_x)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.module_export_snapshot.build_snapshot"
        if _error.span is None:
            _error.span = {"end_byte":583,"end_column":1,"end_line":17,"start_byte":104,"start_column":1,"start_line":7}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.module_export_snapshot.build_snapshot", phase="implementation-call", span={"end_byte":583,"end_column":1,"end_line":17,"start_byte":104,"start_column":1,"start_line":7}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.module_export_snapshot.build_snapshot", phase="implementation-call", span={"end_byte":583,"end_column":1,"end_line":17,"start_byte":104,"start_column":1,"start_line":7}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, ModuleSnapshot, path="$.return")
    if not (((_result).exported_x == exported_x)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.module_export_snapshot.build_snapshot", clause="ensures:1", phase="ensures", span={"end_byte":542,"end_column":44,"end_line":15,"start_byte":503,"start_column":5,"start_line":15}, expected="true", actual="false")
    if not (((_result).module_x == module_x)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.module_export_snapshot.build_snapshot", clause="ensures:2", phase="ensures", span={"end_byte":582,"end_column":40,"end_line":16,"start_byte":547,"start_column":5,"start_line":16}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, ModuleSnapshot, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["ModuleSnapshot", "build_snapshot"]
