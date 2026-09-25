from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_ends_with, _cott_starts_with

from curriculum.workflow_scenario_types import CANCELLED_QUERY, CANCELLED_REQUEST_ID, DRAFT_TEXT, FIRST_SAVE_REVISION, LATEST_SAVE_REVISION, NEW_QUERY, NEW_REQUEST_ID, NEW_RESULT, OLD_QUERY, OLD_REQUEST_ID, PUBLISHED_TEXT, SaveReceipt, SaveSnapshot, SaveStatus, SaveStatus_Flushed, SaveStatus_Queued, SearchResult, SearchSnapshot, SearchStatus, SearchStatus_Loading, SearchStatus_Ready

def begin_search(request_id: U64, query: str) -> SearchSnapshot:
    """Start the snapshot of a new search request. Nothing is applied yet, so the
snapshot is Loading with applied_request_id 0 and an empty result."""
    request_id = _cott_validate_abi(request_id, U64, path="$.request_id")
    query = _cott_validate_abi(query, str, path="$.query")
    if not (_cott_contract_condition(((request_id > 0)), "curriculum.workflow_scenario.begin_search", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.workflow_scenario.begin_search", clause="requires:1", phase="requires", span={"end_byte":1082,"end_column":28,"end_line":49,"start_byte":1059,"start_column":5,"start_line":49}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/workflow_scenario/begin_search.py", "7c84ec979dd3142ffa0797fd05ace26135d870c8bdb5a9acd1c9598dd38fab66", "begin_search", expected_project_name="workflow-scenario", expected_cott_symbol="curriculum.workflow_scenario.begin_search")
        _result = _implementation(request_id, query)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.workflow_scenario.begin_search"
        if _error.span is None:
            _error.span = {"end_byte":1229,"end_column":1,"end_line":57,"start_byte":820,"start_column":1,"start_line":43}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.workflow_scenario.begin_search", phase="implementation-call", span={"end_byte":1229,"end_column":1,"end_line":57,"start_byte":820,"start_column":1,"start_line":43}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.workflow_scenario.begin_search", phase="implementation-call", span={"end_byte":1229,"end_column":1,"end_line":57,"start_byte":820,"start_column":1,"start_line":43}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SearchSnapshot, path="$.return")
    if not (_cott_contract_condition((((_result).request_id == request_id)), "curriculum.workflow_scenario.begin_search", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.begin_search", clause="ensures:2", phase="ensures", span={"end_byte":1127,"end_column":44,"end_line":51,"start_byte":1088,"start_column":5,"start_line":51}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).query == query)), "curriculum.workflow_scenario.begin_search", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.begin_search", clause="ensures:3", phase="ensures", span={"end_byte":1161,"end_column":34,"end_line":52,"start_byte":1132,"start_column":5,"start_line":52}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).status == SearchStatus_Loading())), "curriculum.workflow_scenario.begin_search", "ensures:4")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.begin_search", clause="ensures:4", phase="ensures", span={"end_byte":1211,"end_column":50,"end_line":53,"start_byte":1166,"start_column":5,"start_line":53}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, SearchSnapshot, path="$.return", validator=_cott_validate_abi)
    return _result

async def resolve_search(request_id: U64, query: str) -> SearchResult:
    """Resolve one search request without observing host state. This lesson's
resolver is a deterministic stand-in: the result text is the query followed
by " result", so query "new" resolves to "new result"."""
    request_id = _cott_validate_abi(request_id, U64, path="$.request_id")
    query = _cott_validate_abi(query, str, path="$.query")
    if not (_cott_contract_condition(((request_id > 0)), "curriculum.workflow_scenario.resolve_search", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.workflow_scenario.resolve_search", clause="requires:1", phase="requires", span={"end_byte":1561,"end_column":28,"end_line":64,"start_byte":1538,"start_column":5,"start_line":64}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/workflow_scenario/resolve_search.py", "389a0673cff63b9450863d16f1af70dead7adc765ad21c286bde976cdc00a200", "resolve_search", expected_project_name="workflow-scenario", expected_cott_symbol="curriculum.workflow_scenario.resolve_search")
        _result = await _implementation(request_id, query)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.workflow_scenario.resolve_search"
        if _error.span is None:
            _error.span = {"end_byte":1793,"end_column":1,"end_line":73,"start_byte":1229,"start_column":1,"start_line":57}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.workflow_scenario.resolve_search", phase="implementation-call", span={"end_byte":1793,"end_column":1,"end_line":73,"start_byte":1229,"start_column":1,"start_line":57}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.workflow_scenario.resolve_search", phase="implementation-call", span={"end_byte":1793,"end_column":1,"end_line":73,"start_byte":1229,"start_column":1,"start_line":57}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SearchResult, path="$.return")
    if not (_cott_contract_condition((((_result).request_id == request_id)), "curriculum.workflow_scenario.resolve_search", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.resolve_search", clause="ensures:2", phase="ensures", span={"end_byte":1606,"end_column":44,"end_line":66,"start_byte":1567,"start_column":5,"start_line":66}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).query == query)), "curriculum.workflow_scenario.resolve_search", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.resolve_search", clause="ensures:3", phase="ensures", span={"end_byte":1640,"end_column":34,"end_line":67,"start_byte":1611,"start_column":5,"start_line":67}, expected="true", actual="false")
    if not (_cott_contract_condition(((_cott_starts_with((_result).result, query) and _cott_ends_with((_result).result, " result"))), "curriculum.workflow_scenario.resolve_search", "ensures:4")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.resolve_search", clause="ensures:4", phase="ensures", span={"end_byte":1728,"end_column":88,"end_line":68,"start_byte":1645,"start_column":5,"start_line":68}, expected="true", actual="false")
    if not (_cott_contract_condition(((len((_result).result) == (len(query) + 7))), "curriculum.workflow_scenario.resolve_search", "ensures:5")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.resolve_search", clause="ensures:5", phase="ensures", span={"end_byte":1775,"end_column":47,"end_line":69,"start_byte":1733,"start_column":5,"start_line":69}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, SearchResult, path="$.return", validator=_cott_validate_abi)
    return _result

def apply_search(snapshot: SearchSnapshot, candidate: SearchResult) -> SearchSnapshot:
    """Apply a resolved result only when it belongs to the snapshot's request.
A matching candidate makes the snapshot Ready with the candidate's result;
a candidate for any other request is stale and leaves the snapshot
unchanged, so an older result can never overwrite a newer request."""
    snapshot = _cott_validate_abi(snapshot, SearchSnapshot, path="$.snapshot")
    candidate = _cott_validate_abi(candidate, SearchResult, path="$.candidate")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/workflow_scenario/apply_search.py", "d3a6b3207fd34637d3c7b4614e9b69ed797857bc9084106a64e01d5aa9d36c04", "apply_search", expected_project_name="workflow-scenario", expected_cott_symbol="curriculum.workflow_scenario.apply_search")
        _result = _implementation(snapshot, candidate)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.workflow_scenario.apply_search"
        if _error.span is None:
            _error.span = {"end_byte":2514,"end_column":1,"end_line":87,"start_byte":1793,"start_column":1,"start_line":73}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.workflow_scenario.apply_search", phase="implementation-call", span={"end_byte":2514,"end_column":1,"end_line":87,"start_byte":1793,"start_column":1,"start_line":73}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.workflow_scenario.apply_search", phase="implementation-call", span={"end_byte":2514,"end_column":1,"end_line":87,"start_byte":1793,"start_column":1,"start_line":73}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SearchSnapshot, path="$.return")
    if not (_cott_contract_condition((((_result).request_id == (snapshot).request_id)), "curriculum.workflow_scenario.apply_search", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.apply_search", clause="ensures:1", phase="ensures", span={"end_byte":2281,"end_column":85,"end_line":81,"start_byte":2201,"start_column":5,"start_line":81}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).query == (snapshot).query)), "curriculum.workflow_scenario.apply_search", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.apply_search", clause="ensures:2", phase="ensures", span={"end_byte":2281,"end_column":85,"end_line":81,"start_byte":2201,"start_column":5,"start_line":81}, expected="true", actual="false")
    if not (_cott_contract_condition((((not ((candidate).request_id == (snapshot).request_id)) or (((_result).status == SearchStatus_Ready()) and ((_result).result == (candidate).result)))), "curriculum.workflow_scenario.apply_search", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.apply_search", clause="ensures:3", phase="ensures", span={"end_byte":2416,"end_column":135,"end_line":82,"start_byte":2286,"start_column":5,"start_line":82}, expected="true", actual="false")
    if not (_cott_contract_condition((((not ((candidate).request_id != (snapshot).request_id)) or (_result == snapshot))), "curriculum.workflow_scenario.apply_search", "ensures:4")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.apply_search", clause="ensures:4", phase="ensures", span={"end_byte":2496,"end_column":80,"end_line":83,"start_byte":2421,"start_column":5,"start_line":83}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, SearchSnapshot, path="$.return", validator=_cott_validate_abi)
    return _result

def begin_save(revision: U64, text: str) -> SaveSnapshot:
    """Queue the first save request for revision."""
    revision = _cott_validate_abi(revision, U64, path="$.revision")
    text = _cott_validate_abi(text, str, path="$.text")
    if not (_cott_contract_condition(((revision > 0)), "curriculum.workflow_scenario.begin_save", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.workflow_scenario.begin_save", clause="requires:1", phase="requires", span={"end_byte":2664,"end_column":26,"end_line":92,"start_byte":2643,"start_column":5,"start_line":92}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/workflow_scenario/begin_save.py", "4bb7277ae2cb0e35efea5d3775276578b457499ea6da554d86d3a5dbf7666897", "begin_save", expected_project_name="workflow-scenario", expected_cott_symbol="curriculum.workflow_scenario.begin_save")
        _result = _implementation(revision, text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.workflow_scenario.begin_save"
        if _error.span is None:
            _error.span = {"end_byte":2802,"end_column":1,"end_line":100,"start_byte":2514,"start_column":1,"start_line":87}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.workflow_scenario.begin_save", phase="implementation-call", span={"end_byte":2802,"end_column":1,"end_line":100,"start_byte":2514,"start_column":1,"start_line":87}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.workflow_scenario.begin_save", phase="implementation-call", span={"end_byte":2802,"end_column":1,"end_line":100,"start_byte":2514,"start_column":1,"start_line":87}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SaveSnapshot, path="$.return")
    if not (_cott_contract_condition((((_result).revision == revision)), "curriculum.workflow_scenario.begin_save", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.begin_save", clause="ensures:2", phase="ensures", span={"end_byte":2705,"end_column":40,"end_line":94,"start_byte":2670,"start_column":5,"start_line":94}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).text == text)), "curriculum.workflow_scenario.begin_save", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.begin_save", clause="ensures:3", phase="ensures", span={"end_byte":2737,"end_column":32,"end_line":95,"start_byte":2710,"start_column":5,"start_line":95}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).status == SaveStatus_Queued())), "curriculum.workflow_scenario.begin_save", "ensures:4")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.begin_save", clause="ensures:4", phase="ensures", span={"end_byte":2784,"end_column":47,"end_line":96,"start_byte":2742,"start_column":5,"start_line":96}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, SaveSnapshot, path="$.return", validator=_cott_validate_abi)
    return _result

def request_save(snapshot: SaveSnapshot, revision: U64, text: str) -> SaveSnapshot:
    """Coalesce a save request into the pending snapshot. Only a strictly newer
revision replaces the pending request and queues it; an equal or older
revision is ignored and the snapshot is returned unchanged."""
    snapshot = _cott_validate_abi(snapshot, SaveSnapshot, path="$.snapshot")
    revision = _cott_validate_abi(revision, U64, path="$.revision")
    text = _cott_validate_abi(text, str, path="$.text")
    if not (_cott_contract_condition(((revision > 0)), "curriculum.workflow_scenario.request_save", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="curriculum.workflow_scenario.request_save", clause="requires:1", phase="requires", span={"end_byte":3147,"end_column":26,"end_line":107,"start_byte":3126,"start_column":5,"start_line":107}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/workflow_scenario/request_save.py", "1d8db9b6b295f1d701a0e96e52ddea03735978848f6ab6acadfafbf5af8b23bc", "request_save", expected_project_name="workflow-scenario", expected_cott_symbol="curriculum.workflow_scenario.request_save")
        _result = _implementation(snapshot, revision, text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.workflow_scenario.request_save"
        if _error.span is None:
            _error.span = {"end_byte":3369,"end_column":1,"end_line":114,"start_byte":2802,"start_column":1,"start_line":100}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.workflow_scenario.request_save", phase="implementation-call", span={"end_byte":3369,"end_column":1,"end_line":114,"start_byte":2802,"start_column":1,"start_line":100}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.workflow_scenario.request_save", phase="implementation-call", span={"end_byte":3369,"end_column":1,"end_line":114,"start_byte":2802,"start_column":1,"start_line":100}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SaveSnapshot, path="$.return")
    if not (_cott_contract_condition((((not (revision > (snapshot).revision)) or ((((_result).revision == revision) and ((_result).text == text)) and ((_result).status == SaveStatus_Queued())))), "curriculum.workflow_scenario.request_save", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.request_save", clause="ensures:2", phase="ensures", span={"end_byte":3285,"end_column":137,"end_line":109,"start_byte":3153,"start_column":5,"start_line":109}, expected="true", actual="false")
    if not (_cott_contract_condition((((not (revision <= (snapshot).revision)) or (_result == snapshot))), "curriculum.workflow_scenario.request_save", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.request_save", clause="ensures:3", phase="ensures", span={"end_byte":3351,"end_column":66,"end_line":110,"start_byte":3290,"start_column":5,"start_line":110}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, SaveSnapshot, path="$.return", validator=_cott_validate_abi)
    return _result

def flush_save(snapshot: SaveSnapshot) -> SaveReceipt:
    """Flush the coalesced save request and return its Flushed receipt."""
    snapshot = _cott_validate_abi(snapshot, SaveSnapshot, path="$.snapshot")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/workflow_scenario/flush_save.py", "e537c5449d2141a886417c08f9c44a9b9f492acdd8bf4fbd7ee2da92fe8ef30c", "flush_save", expected_project_name="workflow-scenario", expected_cott_symbol="curriculum.workflow_scenario.flush_save")
        _result = _implementation(snapshot)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.workflow_scenario.flush_save"
        if _error.span is None:
            _error.span = {"end_byte":3668,"end_column":1,"end_line":125,"start_byte":3369,"start_column":1,"start_line":114}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.workflow_scenario.flush_save", phase="implementation-call", span={"end_byte":3668,"end_column":1,"end_line":125,"start_byte":3369,"start_column":1,"start_line":114}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.workflow_scenario.flush_save", phase="implementation-call", span={"end_byte":3668,"end_column":1,"end_line":125,"start_byte":3369,"start_column":1,"start_line":114}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, SaveReceipt, path="$.return")
    if not (_cott_contract_condition((((_result).revision == (snapshot).revision)), "curriculum.workflow_scenario.flush_save", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.flush_save", clause="ensures:1", phase="ensures", span={"end_byte":3561,"end_column":49,"end_line":119,"start_byte":3517,"start_column":5,"start_line":119}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).text == (snapshot).text)), "curriculum.workflow_scenario.flush_save", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.flush_save", clause="ensures:2", phase="ensures", span={"end_byte":3602,"end_column":41,"end_line":120,"start_byte":3566,"start_column":5,"start_line":120}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).status == SaveStatus_Flushed())), "curriculum.workflow_scenario.flush_save", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.workflow_scenario.flush_save", clause="ensures:3", phase="ensures", span={"end_byte":3650,"end_column":48,"end_line":121,"start_byte":3607,"start_column":5,"start_line":121}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, SaveReceipt, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["CANCELLED_QUERY", "CANCELLED_REQUEST_ID", "DRAFT_TEXT", "FIRST_SAVE_REVISION", "LATEST_SAVE_REVISION", "NEW_QUERY", "NEW_REQUEST_ID", "NEW_RESULT", "OLD_QUERY", "OLD_REQUEST_ID", "PUBLISHED_TEXT", "SaveReceipt", "SaveSnapshot", "SaveStatus", "SaveStatus_Flushed", "SaveStatus_Queued", "SearchResult", "SearchSnapshot", "SearchStatus", "SearchStatus_Loading", "SearchStatus_Ready", "apply_search", "begin_save", "begin_search", "flush_save", "request_save", "resolve_search"]
