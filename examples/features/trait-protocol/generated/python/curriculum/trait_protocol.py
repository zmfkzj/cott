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

from curriculum.trait_protocol_types import Completable, Prioritizable, Summarizable, TaskLifecycle, TaskLifecycle_Completed, TaskLifecycle_Pending, TaskView, _cott_curriculum_trait_protocol_Summarizable_Summary_91a0038fc149a52d660ec2d4c914e0f201ef340095a79ffc2c9cd89ad6d2311f, _cott_curriculum_trait_protocol_Summarizable_curriculum_trait_protocol_Summarizable_Summary, _cott_curriculum_trait_protocol_TaskView_curriculum_trait_protocol_Summarizable_Summary

T = TypeVar("T")

async def default_category(receiver: TaskView[T]) -> str:
    """Return the fixed default category "default" for any task view."""
    receiver = _cott_validate_abi(receiver, TaskView[T], path="$.receiver")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/default_category.py", "f929dd3fa5c7d43ebc7c6b49d14a761c8743ff3fe7e0cf9d49a082d034b45215", "default_category", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.default_category")
        _result = await _implementation(receiver)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.trait_protocol.default_category"
        if _error.span is None:
            _error.span = {"end_byte":605,"end_column":1,"end_line":26,"start_byte":408,"start_column":1,"start_line":17}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.default_category", phase="implementation-call", span={"end_byte":605,"end_column":1,"end_line":26,"start_byte":408,"start_column":1,"start_line":17}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.default_category", phase="implementation-call", span={"end_byte":605,"end_column":1,"end_line":26,"start_byte":408,"start_column":1,"start_line":17}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not (_cott_contract_condition(((_result == "default")), "curriculum.trait_protocol.default_category", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.default_category", clause="ensures:1", phase="ensures", span={"end_byte":587,"end_column":32,"end_line":22,"start_byte":560,"start_column":5,"start_line":22}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

async def specialized_display(receiver: SimpleTask) -> str:
    """Return the text "specialized: " immediately followed by receiver.title."""
    receiver = _cott_validate_abi(receiver, SimpleTask, path="$.receiver")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/specialized_display.py", "866830c5cb6c4c5390b0e972239514e160a8c9d5473d40f9f835091ca3e82728", "specialized_display", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.specialized_display")
        _result = await _implementation(receiver)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.trait_protocol.specialized_display"
        if _error.span is None:
            _error.span = {"end_byte":927,"end_column":1,"end_line":37,"start_byte":605,"start_column":1,"start_line":26}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.specialized_display", phase="implementation-call", span={"end_byte":927,"end_column":1,"end_line":37,"start_byte":605,"start_column":1,"start_line":26}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.specialized_display", phase="implementation-call", span={"end_byte":927,"end_column":1,"end_line":37,"start_byte":605,"start_column":1,"start_line":26}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not (_cott_contract_condition((_cott_starts_with(_result, "specialized: ")), "curriculum.trait_protocol.specialized_display", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.specialized_display", clause="ensures:1", phase="ensures", span={"end_byte":811,"end_column":51,"end_line":31,"start_byte":765,"start_column":5,"start_line":31}, expected="true", actual="false")
    if not (_cott_contract_condition((_cott_ends_with(_result, (receiver).title)), "curriculum.trait_protocol.specialized_display", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.specialized_display", clause="ensures:2", phase="ensures", span={"end_byte":859,"end_column":48,"end_line":32,"start_byte":816,"start_column":5,"start_line":32}, expected="true", actual="false")
    if not (_cott_contract_condition(((len(_result) == (len((receiver).title) + 13))), "curriculum.trait_protocol.specialized_display", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.specialized_display", clause="ensures:3", phase="ensures", span={"end_byte":909,"end_column":50,"end_line":33,"start_byte":864,"start_column":5,"start_line":33}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def task_factory() -> type[SimpleTask]:
    """Return the SimpleTask constructor itself as the factory."""
    try:
        _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/task_factory.py", "37fcd3c19ccb8e4225d0e8540632140aa7cc24b9f7debac71d2ed26f635a7f8d", "task_factory", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.task_factory")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.trait_protocol.task_factory"
        if _error.span is None:
            _error.span = {"end_byte":1067,"end_column":1,"end_line":44,"start_byte":927,"start_column":1,"start_line":37}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.task_factory", phase="implementation-call", span={"end_byte":1067,"end_column":1,"end_line":44,"start_byte":927,"start_column":1,"start_line":37}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.task_factory", phase="implementation-call", span={"end_byte":1067,"end_column":1,"end_line":44,"start_byte":927,"start_column":1,"start_line":37}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, type[SimpleTask], path="$.return")
    _result = _cott_wrap_async_protocol(_result, type[SimpleTask], path="$.return", validator=_cott_validate_abi)
    return _result

async def inspect_dyn(item: Dyn[TaskView[str]]) -> str:
    """Return the awaited summary of the dynamically dispatched task view item."""
    item = _cott_validate_abi(item, Dyn[TaskView[str]], path="$.item")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/inspect_dyn.py", "d8f176fb30e6896aabda8ee1b0f4913b723ca7262e384cb5fa6e1b5fff74774d", "inspect_dyn", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.inspect_dyn")
        _result = await _implementation(item)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.trait_protocol.inspect_dyn"
        if _error.span is None:
            _error.span = {"end_byte":1236,"end_column":1,"end_line":51,"start_byte":1067,"start_column":1,"start_line":44}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.inspect_dyn", phase="implementation-call", span={"end_byte":1236,"end_column":1,"end_line":51,"start_byte":1067,"start_column":1,"start_line":44}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.inspect_dyn", phase="implementation-call", span={"end_byte":1236,"end_column":1,"end_line":51,"start_byte":1067,"start_column":1,"start_line":44}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

_cott_default_SimpleTask_category = default_category

_cott_default_SimpleTask_display = specialized_display

@final
class SimpleTask:
    _cott_traits = (Completable, Prioritizable, Summarizable, TaskView,)
    _cott_trait_specs = (Completable, Prioritizable, Summarizable, TaskView[str],)
    title: str
    urgency: I32
    lifecycle: TaskLifecycle
    completion_count: I32
    __slots__ = ("title", "urgency", "lifecycle", "completion_count", "_cott_lock",)

    def __init_subclass__(cls, **_kwargs: object) -> None:
        raise TypeError("SimpleTask is final")

    def __init__(self, title: str, urgency: I32) -> None:
        title = _cott_validate_abi(title, str, path="$.title")
        urgency = _cott_validate_abi(urgency, I32, path="$.urgency")
        if not (_cott_contract_condition(((len(title) > 0)), "curriculum.trait_protocol.SimpleTask", "requires:0")):
            raise CottContractViolation("requires clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="requires:0", phase="requires", span={"end_byte":1844,"end_column":31,"end_line":74,"start_byte":1822,"start_column":9,"start_line":74}, expected="true", actual="false")
        if not (_cott_contract_condition(((urgency >= 0)), "curriculum.trait_protocol.SimpleTask", "requires:1")):
            raise CottContractViolation("requires clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="requires:1", phase="requires", span={"end_byte":1874,"end_column":30,"end_line":75,"start_byte":1853,"start_column":9,"start_line":75}, expected="true", actual="false")
        self.title = _cott_validate_abi(title, str, path="$.title")
        self.urgency = _cott_validate_abi(urgency, I32, path="$.urgency")
        self.lifecycle = _cott_validate_abi(TaskLifecycle_Pending(), TaskLifecycle, path="$.lifecycle")
        self.completion_count = _cott_validate_abi(0, I32, path="$.completion_count")
        self._cott_lock = _CottAsyncRLock()
        if not (_cott_contract_condition((((self).title == title)), "curriculum.trait_protocol.SimpleTask", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="ensures:2", phase="ensures", span={"end_byte":1911,"end_column":36,"end_line":77,"start_byte":1884,"start_column":9,"start_line":77}, expected="true", actual="false")
        if not (_cott_contract_condition((((self).urgency == urgency)), "curriculum.trait_protocol.SimpleTask", "ensures:3")):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="ensures:3", phase="ensures", span={"end_byte":1951,"end_column":40,"end_line":78,"start_byte":1920,"start_column":9,"start_line":78}, expected="true", actual="false")
        if not (_cott_contract_condition(((len((self).title) > 0)), "curriculum.trait_protocol.SimpleTask", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1703,"end_column":33,"end_line":69,"start_byte":1675,"start_column":5,"start_line":69}, expected="true", actual="false")
        if not (_cott_contract_condition((((self).urgency >= 0)), "curriculum.trait_protocol.SimpleTask", "invariant:1")):
            raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1735,"end_column":32,"end_line":70,"start_byte":1708,"start_column":5,"start_line":70}, expected="true", actual="false")
        if not (_cott_contract_condition((((self).completion_count >= 0)), "curriculum.trait_protocol.SimpleTask", "invariant:2")):
            raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1776,"end_column":41,"end_line":71,"start_byte":1740,"start_column":5,"start_line":71}, expected="true", actual="false")

    async def complete(self: SimpleTask) -> bool:
        async with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_lifecycle = self.lifecycle
            _cott_old_completion_count = self.completion_count
            try:
                _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/SimpleTask/complete.py", "272abd3fefd9916a59334699e2764a91c6ad197b8d344cb9d5398bc49cf66db7", "_cott_impl_SimpleTask_complete", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.SimpleTask.complete")
                _result = await _implementation(self)
            except BaseException as _error:
                self.title = _cott_validate_abi(self.title, str, path="$.title")
                self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
                self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
                self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
                if _cott_old_lifecycle is not TaskLifecycle_Pending():
                    raise CottContractViolation("exceptional resource transition source failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="exceptional-transitions", span={"end_byte":2435,"end_column":1,"end_line":100,"start_byte":2152,"start_column":5,"start_line":90}, expected="_cott_old_lifecycle is TaskLifecycle_Pending", actual=repr(_cott_old_lifecycle))
                if self.lifecycle is not _cott_old_lifecycle and self.lifecycle is not TaskLifecycle_Completed():
                    raise CottContractViolation("exceptional resource transition target failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="exceptional-transitions", span={"end_byte":2435,"end_column":1,"end_line":100,"start_byte":2152,"start_column":5,"start_line":90}, expected="self.lifecycle is old or TaskLifecycle_Completed", actual=repr(self.lifecycle))
                if self.title is not _cott_old_title:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="exceptional-frame", span={"end_byte":2435,"end_column":1,"end_line":100,"start_byte":2152,"start_column":5,"start_line":90}, expected="self.title unchanged", actual="self.title changed")
                if self.urgency is not _cott_old_urgency:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="exceptional-frame", span={"end_byte":2435,"end_column":1,"end_line":100,"start_byte":2152,"start_column":5,"start_line":90}, expected="self.urgency unchanged", actual="self.urgency changed")
                if not (_cott_contract_condition(((len((self).title) > 0)), "curriculum.trait_protocol.SimpleTask.complete", "invariant:0")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1703,"end_column":33,"end_line":69,"start_byte":1675,"start_column":5,"start_line":69}, expected="true", actual="false")
                if not (_cott_contract_condition((((self).urgency >= 0)), "curriculum.trait_protocol.SimpleTask.complete", "invariant:1")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1735,"end_column":32,"end_line":70,"start_byte":1708,"start_column":5,"start_line":70}, expected="true", actual="false")
                if not (_cott_contract_condition((((self).completion_count >= 0)), "curriculum.trait_protocol.SimpleTask.complete", "invariant:2")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1776,"end_column":41,"end_line":71,"start_byte":1740,"start_column":5,"start_line":71}, expected="true", actual="false")
                if isinstance(_error, _asyncio.CancelledError):
                    raise
                if isinstance(_error, CottContractViolation):
                    if _error.symbol is None or _error.symbol == "_cott_load":
                        _error.symbol = "curriculum.trait_protocol.SimpleTask.complete"
                    if _error.span is None:
                        _error.span = {"end_byte":2435,"end_column":1,"end_line":100,"start_byte":2152,"start_column":5,"start_line":90}
                    raise
                if isinstance(_error, SystemExit):
                    raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="implementation-call", span={"end_byte":2435,"end_column":1,"end_line":100,"start_byte":2152,"start_column":5,"start_line":90}, expected="ordinary return", actual="SystemExit") from _error
                if isinstance(_error, Exception):
                    raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="implementation-call", span={"end_byte":2435,"end_column":1,"end_line":100,"start_byte":2152,"start_column":5,"start_line":90}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
                raise
            _result = _cott_validate_abi(_result, bool, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
            if _cott_old_lifecycle is not TaskLifecycle_Pending():
                raise CottContractViolation("resource transition source failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="transitions", span={"end_byte":2435,"end_column":1,"end_line":100,"start_byte":2152,"start_column":5,"start_line":90}, expected="self.lifecycle is TaskLifecycle_Pending", actual=repr(_cott_old_lifecycle))
            if self.lifecycle is not TaskLifecycle_Completed():
                raise CottContractViolation("resource transition target failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="transitions", span={"end_byte":2435,"end_column":1,"end_line":100,"start_byte":2152,"start_column":5,"start_line":90}, expected="self.lifecycle is TaskLifecycle_Completed", actual=repr(self.lifecycle))
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="modifies", span={"end_byte":2435,"end_column":1,"end_line":100,"start_byte":2152,"start_column":5,"start_line":90}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="modifies", span={"end_byte":2435,"end_column":1,"end_line":100,"start_byte":2152,"start_column":5,"start_line":90}, expected="self.urgency unchanged", actual="self.urgency changed")
            if not (_cott_contract_condition(((_result == True)), "curriculum.trait_protocol.SimpleTask.complete", "ensures:2")):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", clause="ensures:2", phase="ensures", span={"end_byte":2341,"end_column":31,"end_line":95,"start_byte":2319,"start_column":9,"start_line":95}, expected="true", actual="false")
            if not (_cott_contract_condition((((_cott_old_completion_count + 1) == (self).completion_count)), "curriculum.trait_protocol.SimpleTask.complete", "ensures:3")):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", clause="ensures:3", phase="ensures", span={"end_byte":2413,"end_column":72,"end_line":96,"start_byte":2350,"start_column":9,"start_line":96}, expected="true", actual="false")
            if not (_cott_contract_condition(((len((self).title) > 0)), "curriculum.trait_protocol.SimpleTask.complete", "invariant:0")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1703,"end_column":33,"end_line":69,"start_byte":1675,"start_column":5,"start_line":69}, expected="true", actual="false")
            if not (_cott_contract_condition((((self).urgency >= 0)), "curriculum.trait_protocol.SimpleTask.complete", "invariant:1")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1735,"end_column":32,"end_line":70,"start_byte":1708,"start_column":5,"start_line":70}, expected="true", actual="false")
            if not (_cott_contract_condition((((self).completion_count >= 0)), "curriculum.trait_protocol.SimpleTask.complete", "invariant:2")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1776,"end_column":41,"end_line":71,"start_byte":1740,"start_column":5,"start_line":71}, expected="true", actual="false")
            _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=_cott_validate_abi)
            return _result

    async def priority_level(self: SimpleTask) -> I32:
        async with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_lifecycle = self.lifecycle
            _cott_old_completion_count = self.completion_count
            try:
                _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/SimpleTask/priority_level.py", "679518dc6a9ba9ae44573adc77a9e93ba0c4a515102e13edfb8dd79f0b7f4bb3", "_cott_impl_SimpleTask_priority_level", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.SimpleTask.priority_level")
                _result = await _implementation(self)
            except BaseException as _error:
                self.title = _cott_validate_abi(self.title, str, path="$.title")
                self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
                self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
                self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
                if self.title is not _cott_old_title:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="exceptional-frame", span={"end_byte":2152,"end_column":5,"end_line":90,"start_byte":2050,"start_column":5,"start_line":85}, expected="self.title unchanged", actual="self.title changed")
                if self.urgency is not _cott_old_urgency:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="exceptional-frame", span={"end_byte":2152,"end_column":5,"end_line":90,"start_byte":2050,"start_column":5,"start_line":85}, expected="self.urgency unchanged", actual="self.urgency changed")
                if self.lifecycle is not _cott_old_lifecycle:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="exceptional-frame", span={"end_byte":2152,"end_column":5,"end_line":90,"start_byte":2050,"start_column":5,"start_line":85}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
                if self.completion_count is not _cott_old_completion_count:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="exceptional-frame", span={"end_byte":2152,"end_column":5,"end_line":90,"start_byte":2050,"start_column":5,"start_line":85}, expected="self.completion_count unchanged", actual="self.completion_count changed")
                if not (_cott_contract_condition(((len((self).title) > 0)), "curriculum.trait_protocol.SimpleTask.priority_level", "invariant:0")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1703,"end_column":33,"end_line":69,"start_byte":1675,"start_column":5,"start_line":69}, expected="true", actual="false")
                if not (_cott_contract_condition((((self).urgency >= 0)), "curriculum.trait_protocol.SimpleTask.priority_level", "invariant:1")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1735,"end_column":32,"end_line":70,"start_byte":1708,"start_column":5,"start_line":70}, expected="true", actual="false")
                if not (_cott_contract_condition((((self).completion_count >= 0)), "curriculum.trait_protocol.SimpleTask.priority_level", "invariant:2")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1776,"end_column":41,"end_line":71,"start_byte":1740,"start_column":5,"start_line":71}, expected="true", actual="false")
                if isinstance(_error, _asyncio.CancelledError):
                    raise
                if isinstance(_error, CottContractViolation):
                    if _error.symbol is None or _error.symbol == "_cott_load":
                        _error.symbol = "curriculum.trait_protocol.SimpleTask.priority_level"
                    if _error.span is None:
                        _error.span = {"end_byte":2152,"end_column":5,"end_line":90,"start_byte":2050,"start_column":5,"start_line":85}
                    raise
                if isinstance(_error, SystemExit):
                    raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="implementation-call", span={"end_byte":2152,"end_column":5,"end_line":90,"start_byte":2050,"start_column":5,"start_line":85}, expected="ordinary return", actual="SystemExit") from _error
                if isinstance(_error, Exception):
                    raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="implementation-call", span={"end_byte":2152,"end_column":5,"end_line":90,"start_byte":2050,"start_column":5,"start_line":85}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
                raise
            _result = _cott_validate_abi(_result, I32, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":2152,"end_column":5,"end_line":90,"start_byte":2050,"start_column":5,"start_line":85}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":2152,"end_column":5,"end_line":90,"start_byte":2050,"start_column":5,"start_line":85}, expected="self.urgency unchanged", actual="self.urgency changed")
            if self.lifecycle is not _cott_old_lifecycle:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":2152,"end_column":5,"end_line":90,"start_byte":2050,"start_column":5,"start_line":85}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
            if self.completion_count is not _cott_old_completion_count:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":2152,"end_column":5,"end_line":90,"start_byte":2050,"start_column":5,"start_line":85}, expected="self.completion_count unchanged", actual="self.completion_count changed")
            if not (_cott_contract_condition(((_result == (self).urgency)), "curriculum.trait_protocol.SimpleTask.priority_level", "ensures:0")):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", clause="ensures:0", phase="ensures", span={"end_byte":2126,"end_column":39,"end_line":86,"start_byte":2096,"start_column":9,"start_line":86}, expected="true", actual="false")
            if not (_cott_contract_condition(((len((self).title) > 0)), "curriculum.trait_protocol.SimpleTask.priority_level", "invariant:0")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1703,"end_column":33,"end_line":69,"start_byte":1675,"start_column":5,"start_line":69}, expected="true", actual="false")
            if not (_cott_contract_condition((((self).urgency >= 0)), "curriculum.trait_protocol.SimpleTask.priority_level", "invariant:1")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1735,"end_column":32,"end_line":70,"start_byte":1708,"start_column":5,"start_line":70}, expected="true", actual="false")
            if not (_cott_contract_condition((((self).completion_count >= 0)), "curriculum.trait_protocol.SimpleTask.priority_level", "invariant:2")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1776,"end_column":41,"end_line":71,"start_byte":1740,"start_column":5,"start_line":71}, expected="true", actual="false")
            _result = _cott_wrap_async_protocol(_result, I32, path="$.return", validator=_cott_validate_abi)
            return _result

    async def summary(self: SimpleTask) -> str:
        async with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_lifecycle = self.lifecycle
            _cott_old_completion_count = self.completion_count
            try:
                _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/SimpleTask/summary.py", "f5ff8c7b356d93340d74d4c64a6e5a90db77d7809123ade15198496652e01c65", "_cott_impl_SimpleTask_summary", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.SimpleTask.summary")
                _result = await _implementation(self)
            except BaseException as _error:
                self.title = _cott_validate_abi(self.title, str, path="$.title")
                self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
                self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
                self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
                if self.title is not _cott_old_title:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="exceptional-frame", span={"end_byte":2050,"end_column":5,"end_line":85,"start_byte":1957,"start_column":5,"start_line":80}, expected="self.title unchanged", actual="self.title changed")
                if self.urgency is not _cott_old_urgency:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="exceptional-frame", span={"end_byte":2050,"end_column":5,"end_line":85,"start_byte":1957,"start_column":5,"start_line":80}, expected="self.urgency unchanged", actual="self.urgency changed")
                if self.lifecycle is not _cott_old_lifecycle:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="exceptional-frame", span={"end_byte":2050,"end_column":5,"end_line":85,"start_byte":1957,"start_column":5,"start_line":80}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
                if self.completion_count is not _cott_old_completion_count:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="exceptional-frame", span={"end_byte":2050,"end_column":5,"end_line":85,"start_byte":1957,"start_column":5,"start_line":80}, expected="self.completion_count unchanged", actual="self.completion_count changed")
                if not (_cott_contract_condition(((len((self).title) > 0)), "curriculum.trait_protocol.SimpleTask.summary", "invariant:0")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1703,"end_column":33,"end_line":69,"start_byte":1675,"start_column":5,"start_line":69}, expected="true", actual="false")
                if not (_cott_contract_condition((((self).urgency >= 0)), "curriculum.trait_protocol.SimpleTask.summary", "invariant:1")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1735,"end_column":32,"end_line":70,"start_byte":1708,"start_column":5,"start_line":70}, expected="true", actual="false")
                if not (_cott_contract_condition((((self).completion_count >= 0)), "curriculum.trait_protocol.SimpleTask.summary", "invariant:2")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1776,"end_column":41,"end_line":71,"start_byte":1740,"start_column":5,"start_line":71}, expected="true", actual="false")
                if isinstance(_error, _asyncio.CancelledError):
                    raise
                if isinstance(_error, CottContractViolation):
                    if _error.symbol is None or _error.symbol == "_cott_load":
                        _error.symbol = "curriculum.trait_protocol.SimpleTask.summary"
                    if _error.span is None:
                        _error.span = {"end_byte":2050,"end_column":5,"end_line":85,"start_byte":1957,"start_column":5,"start_line":80}
                    raise
                if isinstance(_error, SystemExit):
                    raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="implementation-call", span={"end_byte":2050,"end_column":5,"end_line":85,"start_byte":1957,"start_column":5,"start_line":80}, expected="ordinary return", actual="SystemExit") from _error
                if isinstance(_error, Exception):
                    raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="implementation-call", span={"end_byte":2050,"end_column":5,"end_line":85,"start_byte":1957,"start_column":5,"start_line":80}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
                raise
            _result = _cott_validate_abi(_result, str, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":2050,"end_column":5,"end_line":85,"start_byte":1957,"start_column":5,"start_line":80}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":2050,"end_column":5,"end_line":85,"start_byte":1957,"start_column":5,"start_line":80}, expected="self.urgency unchanged", actual="self.urgency changed")
            if self.lifecycle is not _cott_old_lifecycle:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":2050,"end_column":5,"end_line":85,"start_byte":1957,"start_column":5,"start_line":80}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
            if self.completion_count is not _cott_old_completion_count:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":2050,"end_column":5,"end_line":85,"start_byte":1957,"start_column":5,"start_line":80}, expected="self.completion_count unchanged", actual="self.completion_count changed")
            if not (_cott_contract_condition(((_result == (self).title)), "curriculum.trait_protocol.SimpleTask.summary", "ensures:0")):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", clause="ensures:0", phase="ensures", span={"end_byte":2024,"end_column":37,"end_line":81,"start_byte":1996,"start_column":9,"start_line":81}, expected="true", actual="false")
            if not (_cott_contract_condition(((len((self).title) > 0)), "curriculum.trait_protocol.SimpleTask.summary", "invariant:0")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1703,"end_column":33,"end_line":69,"start_byte":1675,"start_column":5,"start_line":69}, expected="true", actual="false")
            if not (_cott_contract_condition((((self).urgency >= 0)), "curriculum.trait_protocol.SimpleTask.summary", "invariant:1")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1735,"end_column":32,"end_line":70,"start_byte":1708,"start_column":5,"start_line":70}, expected="true", actual="false")
            if not (_cott_contract_condition((((self).completion_count >= 0)), "curriculum.trait_protocol.SimpleTask.summary", "invariant:2")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1776,"end_column":41,"end_line":71,"start_byte":1740,"start_column":5,"start_line":71}, expected="true", actual="false")
            _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
            return _result

    async def category(self: SimpleTask) -> str:
        async with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_lifecycle = self.lifecycle
            _cott_old_completion_count = self.completion_count
            try:
                _result = await _cott_default_SimpleTask_category(self)
            except BaseException as _error:
                self.title = _cott_validate_abi(self.title, str, path="$.title")
                self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
                self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
                self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
                if self.title is not _cott_old_title:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.category", phase="exceptional-frame", span={"end_byte":350,"end_column":80,"end_line":12,"start_byte":275,"start_column":5,"start_line":12}, expected="self.title unchanged", actual="self.title changed")
                if self.urgency is not _cott_old_urgency:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.category", phase="exceptional-frame", span={"end_byte":350,"end_column":80,"end_line":12,"start_byte":275,"start_column":5,"start_line":12}, expected="self.urgency unchanged", actual="self.urgency changed")
                if self.lifecycle is not _cott_old_lifecycle:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.category", phase="exceptional-frame", span={"end_byte":350,"end_column":80,"end_line":12,"start_byte":275,"start_column":5,"start_line":12}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
                if self.completion_count is not _cott_old_completion_count:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.category", phase="exceptional-frame", span={"end_byte":350,"end_column":80,"end_line":12,"start_byte":275,"start_column":5,"start_line":12}, expected="self.completion_count unchanged", actual="self.completion_count changed")
                if not (_cott_contract_condition(((len((self).title) > 0)), "curriculum.trait_protocol.SimpleTask.category", "invariant:0")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1703,"end_column":33,"end_line":69,"start_byte":1675,"start_column":5,"start_line":69}, expected="true", actual="false")
                if not (_cott_contract_condition((((self).urgency >= 0)), "curriculum.trait_protocol.SimpleTask.category", "invariant:1")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1735,"end_column":32,"end_line":70,"start_byte":1708,"start_column":5,"start_line":70}, expected="true", actual="false")
                if not (_cott_contract_condition((((self).completion_count >= 0)), "curriculum.trait_protocol.SimpleTask.category", "invariant:2")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1776,"end_column":41,"end_line":71,"start_byte":1740,"start_column":5,"start_line":71}, expected="true", actual="false")
                if isinstance(_error, _asyncio.CancelledError):
                    raise
                if isinstance(_error, CottContractViolation):
                    if _error.symbol is None or _error.symbol == "_cott_load":
                        _error.symbol = "curriculum.trait_protocol.SimpleTask.category"
                    if _error.span is None:
                        _error.span = {"end_byte":350,"end_column":80,"end_line":12,"start_byte":275,"start_column":5,"start_line":12}
                    raise
                if isinstance(_error, SystemExit):
                    raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.category", phase="implementation-call", span={"end_byte":350,"end_column":80,"end_line":12,"start_byte":275,"start_column":5,"start_line":12}, expected="ordinary return", actual="SystemExit") from _error
                if isinstance(_error, Exception):
                    raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.category", phase="implementation-call", span={"end_byte":350,"end_column":80,"end_line":12,"start_byte":275,"start_column":5,"start_line":12}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
                raise
            _result = _cott_validate_abi(_result, str, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.category", phase="modifies", span={"end_byte":350,"end_column":80,"end_line":12,"start_byte":275,"start_column":5,"start_line":12}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.category", phase="modifies", span={"end_byte":350,"end_column":80,"end_line":12,"start_byte":275,"start_column":5,"start_line":12}, expected="self.urgency unchanged", actual="self.urgency changed")
            if self.lifecycle is not _cott_old_lifecycle:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.category", phase="modifies", span={"end_byte":350,"end_column":80,"end_line":12,"start_byte":275,"start_column":5,"start_line":12}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
            if self.completion_count is not _cott_old_completion_count:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.category", phase="modifies", span={"end_byte":350,"end_column":80,"end_line":12,"start_byte":275,"start_column":5,"start_line":12}, expected="self.completion_count unchanged", actual="self.completion_count changed")
            if not (_cott_contract_condition(((len((self).title) > 0)), "curriculum.trait_protocol.SimpleTask.category", "invariant:0")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1703,"end_column":33,"end_line":69,"start_byte":1675,"start_column":5,"start_line":69}, expected="true", actual="false")
            if not (_cott_contract_condition((((self).urgency >= 0)), "curriculum.trait_protocol.SimpleTask.category", "invariant:1")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1735,"end_column":32,"end_line":70,"start_byte":1708,"start_column":5,"start_line":70}, expected="true", actual="false")
            if not (_cott_contract_condition((((self).completion_count >= 0)), "curriculum.trait_protocol.SimpleTask.category", "invariant:2")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1776,"end_column":41,"end_line":71,"start_byte":1740,"start_column":5,"start_line":71}, expected="true", actual="false")
            _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
            return _result

    async def display(self: SimpleTask) -> str:
        async with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_lifecycle = self.lifecycle
            _cott_old_completion_count = self.completion_count
            try:
                _result = await _cott_default_SimpleTask_display(self)
            except BaseException as _error:
                self.title = _cott_validate_abi(self.title, str, path="$.title")
                self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
                self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
                self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
                if self.title is not _cott_old_title:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.display", phase="exceptional-frame", span={"end_byte":270,"end_column":32,"end_line":11,"start_byte":243,"start_column":5,"start_line":11}, expected="self.title unchanged", actual="self.title changed")
                if self.urgency is not _cott_old_urgency:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.display", phase="exceptional-frame", span={"end_byte":270,"end_column":32,"end_line":11,"start_byte":243,"start_column":5,"start_line":11}, expected="self.urgency unchanged", actual="self.urgency changed")
                if self.lifecycle is not _cott_old_lifecycle:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.display", phase="exceptional-frame", span={"end_byte":270,"end_column":32,"end_line":11,"start_byte":243,"start_column":5,"start_line":11}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
                if self.completion_count is not _cott_old_completion_count:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.display", phase="exceptional-frame", span={"end_byte":270,"end_column":32,"end_line":11,"start_byte":243,"start_column":5,"start_line":11}, expected="self.completion_count unchanged", actual="self.completion_count changed")
                if not (_cott_contract_condition(((len((self).title) > 0)), "curriculum.trait_protocol.SimpleTask.display", "invariant:0")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1703,"end_column":33,"end_line":69,"start_byte":1675,"start_column":5,"start_line":69}, expected="true", actual="false")
                if not (_cott_contract_condition((((self).urgency >= 0)), "curriculum.trait_protocol.SimpleTask.display", "invariant:1")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1735,"end_column":32,"end_line":70,"start_byte":1708,"start_column":5,"start_line":70}, expected="true", actual="false")
                if not (_cott_contract_condition((((self).completion_count >= 0)), "curriculum.trait_protocol.SimpleTask.display", "invariant:2")):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1776,"end_column":41,"end_line":71,"start_byte":1740,"start_column":5,"start_line":71}, expected="true", actual="false")
                if isinstance(_error, _asyncio.CancelledError):
                    raise
                if isinstance(_error, CottContractViolation):
                    if _error.symbol is None or _error.symbol == "_cott_load":
                        _error.symbol = "curriculum.trait_protocol.SimpleTask.display"
                    if _error.span is None:
                        _error.span = {"end_byte":270,"end_column":32,"end_line":11,"start_byte":243,"start_column":5,"start_line":11}
                    raise
                if isinstance(_error, SystemExit):
                    raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.display", phase="implementation-call", span={"end_byte":270,"end_column":32,"end_line":11,"start_byte":243,"start_column":5,"start_line":11}, expected="ordinary return", actual="SystemExit") from _error
                if isinstance(_error, Exception):
                    raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.display", phase="implementation-call", span={"end_byte":270,"end_column":32,"end_line":11,"start_byte":243,"start_column":5,"start_line":11}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
                raise
            _result = _cott_validate_abi(_result, str, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.display", phase="modifies", span={"end_byte":270,"end_column":32,"end_line":11,"start_byte":243,"start_column":5,"start_line":11}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.display", phase="modifies", span={"end_byte":270,"end_column":32,"end_line":11,"start_byte":243,"start_column":5,"start_line":11}, expected="self.urgency unchanged", actual="self.urgency changed")
            if self.lifecycle is not _cott_old_lifecycle:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.display", phase="modifies", span={"end_byte":270,"end_column":32,"end_line":11,"start_byte":243,"start_column":5,"start_line":11}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
            if self.completion_count is not _cott_old_completion_count:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.display", phase="modifies", span={"end_byte":270,"end_column":32,"end_line":11,"start_byte":243,"start_column":5,"start_line":11}, expected="self.completion_count unchanged", actual="self.completion_count changed")
            if not (_cott_contract_condition(((len((self).title) > 0)), "curriculum.trait_protocol.SimpleTask.display", "invariant:0")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1703,"end_column":33,"end_line":69,"start_byte":1675,"start_column":5,"start_line":69}, expected="true", actual="false")
            if not (_cott_contract_condition((((self).urgency >= 0)), "curriculum.trait_protocol.SimpleTask.display", "invariant:1")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1735,"end_column":32,"end_line":70,"start_byte":1708,"start_column":5,"start_line":70}, expected="true", actual="false")
            if not (_cott_contract_condition((((self).completion_count >= 0)), "curriculum.trait_protocol.SimpleTask.display", "invariant:2")):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1776,"end_column":41,"end_line":71,"start_byte":1740,"start_column":5,"start_line":71}, expected="true", actual="false")
            _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
            return _result

__all__ = ["Completable", "Prioritizable", "SimpleTask", "Summarizable", "TaskLifecycle", "TaskLifecycle_Completed", "TaskLifecycle_Pending", "TaskView", "default_category", "inspect_dyn", "specialized_display", "task_factory"]
