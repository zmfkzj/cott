from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from curriculum.workflow_scenario_types import CANCELLED_QUERY, CANCELLED_REQUEST_ID, DRAFT_TEXT, FIRST_SAVE_REVISION, LATEST_SAVE_REVISION, NEW_QUERY, NEW_REQUEST_ID, NEW_RESULT, OLD_QUERY, OLD_REQUEST_ID, PUBLISHED_TEXT, SaveReceipt, SaveSnapshot, SaveStatus, SaveStatus_Flushed, SaveStatus_Queued, SearchResult, SearchSnapshot, SearchStatus, SearchStatus_Loading, SearchStatus_Ready

def begin_search(request_id: U64, query: str) -> SearchSnapshot:
    """Start an immutable public search snapshot for the supplied request."""
    request_id = _cott_validate_abi(request_id, U64, path="$.request_id")
    query = _cott_validate_abi(query, str, path="$.query")
    if not (_cott_contract_condition(((request_id > 0)), "curriculum.workflow_scenario.begin_search", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.workflow_scenario.begin_search", clause="requires:1", phase="requires", span={"end_byte":851,"end_column":28,"end_line":47,"start_byte":828,"start_column":5,"start_line":47}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/workflow_scenario/begin_search.py", "7c84ec979dd3142ffa0797fd05ace26135d870c8bdb5a9acd1c9598dd38fab66", "begin_search", expected_project_name="workflow-scenario", expected_cott_symbol="curriculum.workflow_scenario.begin_search")
        _result = _implementation(request_id, query)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.workflow_scenario.begin_search"
        if _error.span is None:
            _error.span = {"end_byte":869,"end_column":1,"end_line":51,"start_byte":667,"start_column":1,"start_line":42}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.workflow_scenario.begin_search", phase="implementation-call", span={"end_byte":869,"end_column":1,"end_line":51,"start_byte":667,"start_column":1,"start_line":42}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.workflow_scenario.begin_search", phase="implementation-call", span={"end_byte":869,"end_column":1,"end_line":51,"start_byte":667,"start_column":1,"start_line":42}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SearchSnapshot, path="$.return")
    _result = _cott_wrap_async_protocol(_result, SearchSnapshot, path="$.return", validator=_cott_validate_abi)
    return _result

async def resolve_search(request_id: U64, query: str) -> SearchResult:
    """Resolve one immutable search result without observing host state."""
    request_id = _cott_validate_abi(request_id, U64, path="$.request_id")
    query = _cott_validate_abi(query, str, path="$.query")
    if not (_cott_contract_condition(((request_id > 0)), "curriculum.workflow_scenario.resolve_search", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.workflow_scenario.resolve_search", clause="requires:1", phase="requires", span={"end_byte":1057,"end_column":28,"end_line":56,"start_byte":1034,"start_column":5,"start_line":56}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/workflow_scenario/resolve_search.py", "b0a372753b6b9ed39beaa837c3a27f80dae61e52d34f7dffc1b2e55235b0a80f", "resolve_search", expected_project_name="workflow-scenario", expected_cott_symbol="curriculum.workflow_scenario.resolve_search")
        _result = await _implementation(request_id, query)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.workflow_scenario.resolve_search"
        if _error.span is None:
            _error.span = {"end_byte":1075,"end_column":1,"end_line":60,"start_byte":869,"start_column":1,"start_line":51}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.workflow_scenario.resolve_search", phase="implementation-call", span={"end_byte":1075,"end_column":1,"end_line":60,"start_byte":869,"start_column":1,"start_line":51}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.workflow_scenario.resolve_search", phase="implementation-call", span={"end_byte":1075,"end_column":1,"end_line":60,"start_byte":869,"start_column":1,"start_line":51}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SearchResult, path="$.return")
    _result = _cott_wrap_async_protocol(_result, SearchResult, path="$.return", validator=_cott_validate_abi)
    return _result

def apply_search(snapshot: SearchSnapshot, candidate: SearchResult) -> SearchSnapshot:
    """Apply a result only when it still belongs to the snapshot's newest request."""
    snapshot = _cott_validate_abi(snapshot, SearchSnapshot, path="$.snapshot")
    candidate = _cott_validate_abi(candidate, SearchResult, path="$.candidate")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/workflow_scenario/apply_search.py", "5f176b09ac2f84d72d5bca317d5eeeaf82319bb959eba5d8f7c0ed22e62d3433", "apply_search", expected_project_name="workflow-scenario", expected_cott_symbol="curriculum.workflow_scenario.apply_search")
        _result = _implementation(snapshot, candidate)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.workflow_scenario.apply_search"
        if _error.span is None:
            _error.span = {"end_byte":1278,"end_column":1,"end_line":67,"start_byte":1075,"start_column":1,"start_line":60}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.workflow_scenario.apply_search", phase="implementation-call", span={"end_byte":1278,"end_column":1,"end_line":67,"start_byte":1075,"start_column":1,"start_line":60}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.workflow_scenario.apply_search", phase="implementation-call", span={"end_byte":1278,"end_column":1,"end_line":67,"start_byte":1075,"start_column":1,"start_line":60}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SearchSnapshot, path="$.return")
    _result = _cott_wrap_async_protocol(_result, SearchSnapshot, path="$.return", validator=_cott_validate_abi)
    return _result

def begin_save(revision: U64, text: str) -> SaveSnapshot:
    """Queue the first immutable save request."""
    revision = _cott_validate_abi(revision, U64, path="$.revision")
    text = _cott_validate_abi(text, str, path="$.text")
    if not (_cott_contract_condition(((revision > 0)), "curriculum.workflow_scenario.begin_save", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.workflow_scenario.begin_save", clause="requires:1", phase="requires", span={"end_byte":1425,"end_column":26,"end_line":72,"start_byte":1404,"start_column":5,"start_line":72}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/workflow_scenario/begin_save.py", "4bb7277ae2cb0e35efea5d3775276578b457499ea6da554d86d3a5dbf7666897", "begin_save", expected_project_name="workflow-scenario", expected_cott_symbol="curriculum.workflow_scenario.begin_save")
        _result = _implementation(revision, text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.workflow_scenario.begin_save"
        if _error.span is None:
            _error.span = {"end_byte":1443,"end_column":1,"end_line":76,"start_byte":1278,"start_column":1,"start_line":67}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.workflow_scenario.begin_save", phase="implementation-call", span={"end_byte":1443,"end_column":1,"end_line":76,"start_byte":1278,"start_column":1,"start_line":67}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.workflow_scenario.begin_save", phase="implementation-call", span={"end_byte":1443,"end_column":1,"end_line":76,"start_byte":1278,"start_column":1,"start_line":67}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SaveSnapshot, path="$.return")
    _result = _cott_wrap_async_protocol(_result, SaveSnapshot, path="$.return", validator=_cott_validate_abi)
    return _result

def request_save(snapshot: SaveSnapshot, revision: U64, text: str) -> SaveSnapshot:
    """Coalesce a newer save request into the public queued snapshot."""
    snapshot = _cott_validate_abi(snapshot, SaveSnapshot, path="$.snapshot")
    revision = _cott_validate_abi(revision, U64, path="$.revision")
    text = _cott_validate_abi(text, str, path="$.text")
    if not (_cott_contract_condition(((revision > 0)), "curriculum.workflow_scenario.request_save", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.workflow_scenario.request_save", clause="requires:1", phase="requires", span={"end_byte":1639,"end_column":26,"end_line":81,"start_byte":1618,"start_column":5,"start_line":81}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/workflow_scenario/request_save.py", "dee7998910630f24e0be39e037e79190358c878388c748a62938e58f7ea620a7", "request_save", expected_project_name="workflow-scenario", expected_cott_symbol="curriculum.workflow_scenario.request_save")
        _result = _implementation(snapshot, revision, text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.workflow_scenario.request_save"
        if _error.span is None:
            _error.span = {"end_byte":1657,"end_column":1,"end_line":85,"start_byte":1443,"start_column":1,"start_line":76}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.workflow_scenario.request_save", phase="implementation-call", span={"end_byte":1657,"end_column":1,"end_line":85,"start_byte":1443,"start_column":1,"start_line":76}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.workflow_scenario.request_save", phase="implementation-call", span={"end_byte":1657,"end_column":1,"end_line":85,"start_byte":1443,"start_column":1,"start_line":76}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SaveSnapshot, path="$.return")
    _result = _cott_wrap_async_protocol(_result, SaveSnapshot, path="$.return", validator=_cott_validate_abi)
    return _result

def flush_save(snapshot: SaveSnapshot) -> SaveReceipt:
    """Return the public receipt for the currently coalesced save request."""
    snapshot = _cott_validate_abi(snapshot, SaveSnapshot, path="$.snapshot")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/workflow_scenario/flush_save.py", "e537c5449d2141a886417c08f9c44a9b9f492acdd8bf4fbd7ee2da92fe8ef30c", "flush_save", expected_project_name="workflow-scenario", expected_cott_symbol="curriculum.workflow_scenario.flush_save")
        _result = _implementation(snapshot)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.workflow_scenario.flush_save"
        if _error.span is None:
            _error.span = {"end_byte":1820,"end_column":1,"end_line":92,"start_byte":1657,"start_column":1,"start_line":85}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.workflow_scenario.flush_save", phase="implementation-call", span={"end_byte":1820,"end_column":1,"end_line":92,"start_byte":1657,"start_column":1,"start_line":85}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.workflow_scenario.flush_save", phase="implementation-call", span={"end_byte":1820,"end_column":1,"end_line":92,"start_byte":1657,"start_column":1,"start_line":85}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SaveReceipt, path="$.return")
    _result = _cott_wrap_async_protocol(_result, SaveReceipt, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["CANCELLED_QUERY", "CANCELLED_REQUEST_ID", "DRAFT_TEXT", "FIRST_SAVE_REVISION", "LATEST_SAVE_REVISION", "NEW_QUERY", "NEW_REQUEST_ID", "NEW_RESULT", "OLD_QUERY", "OLD_REQUEST_ID", "PUBLISHED_TEXT", "SaveReceipt", "SaveSnapshot", "SaveStatus", "SaveStatus_Flushed", "SaveStatus_Queued", "SearchResult", "SearchSnapshot", "SearchStatus", "SearchStatus_Loading", "SearchStatus_Ready", "apply_search", "begin_save", "begin_search", "flush_save", "request_save", "resolve_search"]
