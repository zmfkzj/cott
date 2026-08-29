from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.trait_protocol_types import Completable, Prioritizable, Summarizable, TaskLifecycle, TaskLifecycle_Completed, TaskLifecycle_Pending, TaskView, _cott_curriculum_trait_protocol_Summarizable_Summary_91a0038fc149a52d660ec2d4c914e0f201ef340095a79ffc2c9cd89ad6d2311f, _cott_curriculum_trait_protocol_Summarizable_curriculum_trait_protocol_Summarizable_Summary, _cott_curriculum_trait_protocol_TaskView_curriculum_trait_protocol_Summarizable_Summary

T = TypeVar("T")

async def default_category(receiver: TaskView[T]) -> str:
    receiver = _cott_validate_abi(receiver, TaskView[T], path="$.receiver")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/default_category.py", "0f96a9f763965a83e7ce0b63dc264dbb593eec656b12751f42e5592888c993d7", "default_category", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.default_category")
        _result = await _implementation(receiver)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.trait_protocol.default_category"
        if _error.span is None:
            _error.span = {"end_byte":484,"end_column":1,"end_line":20,"start_byte":408,"start_column":1,"start_line":17}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.default_category", phase="implementation-call", span={"end_byte":484,"end_column":1,"end_line":20,"start_byte":408,"start_column":1,"start_line":17}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.default_category", phase="implementation-call", span={"end_byte":484,"end_column":1,"end_line":20,"start_byte":408,"start_column":1,"start_line":17}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

async def specialized_display(receiver: SimpleTask) -> str:
    receiver = _cott_validate_abi(receiver, SimpleTask, path="$.receiver")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/specialized_display.py", "1d868ab442f2268702870583134a20ccc854cbab4cf84db6a64972ba85d7b5b1", "specialized_display", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.specialized_display")
        _result = await _implementation(receiver)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.trait_protocol.specialized_display"
        if _error.span is None:
            _error.span = {"end_byte":559,"end_column":1,"end_line":23,"start_byte":484,"start_column":1,"start_line":20}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.specialized_display", phase="implementation-call", span={"end_byte":559,"end_column":1,"end_line":23,"start_byte":484,"start_column":1,"start_line":20}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.specialized_display", phase="implementation-call", span={"end_byte":559,"end_column":1,"end_line":23,"start_byte":484,"start_column":1,"start_line":20}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def task_factory() -> type[SimpleTask]:
    try:
        _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/task_factory.py", "f52620e94324be5221c5c3484c7085c59bc5a7ef0d7f83d1b23400ea50f1afa4", "task_factory", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.task_factory")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.trait_protocol.task_factory"
        if _error.span is None:
            _error.span = {"end_byte":617,"end_column":1,"end_line":26,"start_byte":559,"start_column":1,"start_line":23}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.task_factory", phase="implementation-call", span={"end_byte":617,"end_column":1,"end_line":26,"start_byte":559,"start_column":1,"start_line":23}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.task_factory", phase="implementation-call", span={"end_byte":617,"end_column":1,"end_line":26,"start_byte":559,"start_column":1,"start_line":23}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, type[SimpleTask], path="$.return")
    _result = _cott_wrap_async_protocol(_result, type[SimpleTask], path="$.return", validator=_cott_validate_abi)
    return _result

async def inspect_dyn(item: Dyn[TaskView[str]]) -> str:
    item = _cott_validate_abi(item, Dyn[TaskView[str]], path="$.item")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/inspect_dyn.py", "e45e94b9aa9476d9fb70ba1a198be6db88270bb401907461fc01acacd0fd58b2", "inspect_dyn", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.inspect_dyn")
        _result = await _implementation(item)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.trait_protocol.inspect_dyn"
        if _error.span is None:
            _error.span = {"end_byte":688,"end_column":1,"end_line":29,"start_byte":617,"start_column":1,"start_line":26}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.inspect_dyn", phase="implementation-call", span={"end_byte":688,"end_column":1,"end_line":29,"start_byte":617,"start_column":1,"start_line":26}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.inspect_dyn", phase="implementation-call", span={"end_byte":688,"end_column":1,"end_line":29,"start_byte":617,"start_column":1,"start_line":26}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
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
        if not ((len(title) > 0)):
            raise CottContractViolation("requires clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="requires:0", phase="requires", span={"end_byte":1296,"end_column":31,"end_line":52,"start_byte":1274,"start_column":9,"start_line":52}, expected="true", actual="false")
        if not ((urgency >= 0)):
            raise CottContractViolation("requires clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="requires:1", phase="requires", span={"end_byte":1326,"end_column":30,"end_line":53,"start_byte":1305,"start_column":9,"start_line":53}, expected="true", actual="false")
        self.title = _cott_validate_abi(title, str, path="$.title")
        self.urgency = _cott_validate_abi(urgency, I32, path="$.urgency")
        self.lifecycle = _cott_validate_abi(TaskLifecycle_Pending(), TaskLifecycle, path="$.lifecycle")
        self.completion_count = _cott_validate_abi(0, I32, path="$.completion_count")
        self._cott_lock = _CottAsyncRLock()
        if not (((self).title == title)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="ensures:2", phase="ensures", span={"end_byte":1363,"end_column":36,"end_line":55,"start_byte":1336,"start_column":9,"start_line":55}, expected="true", actual="false")
        if not (((self).urgency == urgency)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="ensures:3", phase="ensures", span={"end_byte":1403,"end_column":40,"end_line":56,"start_byte":1372,"start_column":9,"start_line":56}, expected="true", actual="false")
        if not ((len((self).title) > 0)):
            raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1155,"end_column":33,"end_line":47,"start_byte":1127,"start_column":5,"start_line":47}, expected="true", actual="false")
        if not (((self).urgency >= 0)):
            raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1187,"end_column":32,"end_line":48,"start_byte":1160,"start_column":5,"start_line":48}, expected="true", actual="false")
        if not (((self).completion_count >= 0)):
            raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1228,"end_column":41,"end_line":49,"start_byte":1192,"start_column":5,"start_line":49}, expected="true", actual="false")

    async def complete(self: SimpleTask) -> bool:
        async with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_lifecycle = self.lifecycle
            _cott_old_completion_count = self.completion_count
            try:
                _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/SimpleTask/complete.py", "c2eeca85cc7bc2ee21ef4c92a8cd59a30715ec11af53e613faa70f5d3693f6c5", "_cott_impl_SimpleTask_complete", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.SimpleTask.complete")
                _result = await _implementation(self)
            except BaseException as _error:
                self.title = _cott_validate_abi(self.title, str, path="$.title")
                self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
                self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
                self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
                if _cott_old_lifecycle is not TaskLifecycle_Pending():
                    raise CottContractViolation("exceptional resource transition source failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="exceptional-transitions", span={"end_byte":1880,"end_column":1,"end_line":77,"start_byte":1598,"start_column":5,"start_line":68}, expected="_cott_old_lifecycle is TaskLifecycle_Pending", actual=repr(_cott_old_lifecycle))
                if self.lifecycle is not _cott_old_lifecycle and self.lifecycle is not TaskLifecycle_Completed():
                    raise CottContractViolation("exceptional resource transition target failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="exceptional-transitions", span={"end_byte":1880,"end_column":1,"end_line":77,"start_byte":1598,"start_column":5,"start_line":68}, expected="self.lifecycle is old or TaskLifecycle_Completed", actual=repr(self.lifecycle))
                if self.title is not _cott_old_title:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="exceptional-frame", span={"end_byte":1880,"end_column":1,"end_line":77,"start_byte":1598,"start_column":5,"start_line":68}, expected="self.title unchanged", actual="self.title changed")
                if self.urgency is not _cott_old_urgency:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="exceptional-frame", span={"end_byte":1880,"end_column":1,"end_line":77,"start_byte":1598,"start_column":5,"start_line":68}, expected="self.urgency unchanged", actual="self.urgency changed")
                if not ((len((self).title) > 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1155,"end_column":33,"end_line":47,"start_byte":1127,"start_column":5,"start_line":47}, expected="true", actual="false")
                if not (((self).urgency >= 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1187,"end_column":32,"end_line":48,"start_byte":1160,"start_column":5,"start_line":48}, expected="true", actual="false")
                if not (((self).completion_count >= 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1228,"end_column":41,"end_line":49,"start_byte":1192,"start_column":5,"start_line":49}, expected="true", actual="false")
                if isinstance(_error, _asyncio.CancelledError):
                    raise
                if isinstance(_error, CottContractViolation):
                    if _error.symbol is None or _error.symbol == "_cott_load":
                        _error.symbol = "curriculum.trait_protocol.SimpleTask.complete"
                    if _error.span is None:
                        _error.span = {"end_byte":1880,"end_column":1,"end_line":77,"start_byte":1598,"start_column":5,"start_line":68}
                    raise
                if isinstance(_error, SystemExit):
                    raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="implementation-call", span={"end_byte":1880,"end_column":1,"end_line":77,"start_byte":1598,"start_column":5,"start_line":68}, expected="ordinary return", actual="SystemExit") from _error
                if isinstance(_error, Exception):
                    raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="implementation-call", span={"end_byte":1880,"end_column":1,"end_line":77,"start_byte":1598,"start_column":5,"start_line":68}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
                raise
            _result = _cott_validate_abi(_result, bool, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
            if _cott_old_lifecycle is not TaskLifecycle_Pending():
                raise CottContractViolation("resource transition source failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="transitions", span={"end_byte":1880,"end_column":1,"end_line":77,"start_byte":1598,"start_column":5,"start_line":68}, expected="self.lifecycle is TaskLifecycle_Pending", actual=repr(_cott_old_lifecycle))
            if self.lifecycle is not TaskLifecycle_Completed():
                raise CottContractViolation("resource transition target failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="transitions", span={"end_byte":1880,"end_column":1,"end_line":77,"start_byte":1598,"start_column":5,"start_line":68}, expected="self.lifecycle is TaskLifecycle_Completed", actual=repr(self.lifecycle))
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="modifies", span={"end_byte":1880,"end_column":1,"end_line":77,"start_byte":1598,"start_column":5,"start_line":68}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="modifies", span={"end_byte":1880,"end_column":1,"end_line":77,"start_byte":1598,"start_column":5,"start_line":68}, expected="self.urgency unchanged", actual="self.urgency changed")
            if not ((_result == True)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", clause="ensures:2", phase="ensures", span={"end_byte":1787,"end_column":31,"end_line":73,"start_byte":1765,"start_column":9,"start_line":73}, expected="true", actual="false")
            if not (((_cott_old_completion_count + 1) == (self).completion_count)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", clause="ensures:3", phase="ensures", span={"end_byte":1859,"end_column":72,"end_line":74,"start_byte":1796,"start_column":9,"start_line":74}, expected="true", actual="false")
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1155,"end_column":33,"end_line":47,"start_byte":1127,"start_column":5,"start_line":47}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1187,"end_column":32,"end_line":48,"start_byte":1160,"start_column":5,"start_line":48}, expected="true", actual="false")
            if not (((self).completion_count >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1228,"end_column":41,"end_line":49,"start_byte":1192,"start_column":5,"start_line":49}, expected="true", actual="false")
            _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=_cott_validate_abi)
            return _result

    async def priority_level(self: SimpleTask) -> I32:
        async with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_lifecycle = self.lifecycle
            _cott_old_completion_count = self.completion_count
            try:
                _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/SimpleTask/priority_level.py", "c602f09d3f61a255dfd819dc2c15a6dd0bd89e9fb69277717f9ccaa57259f0be", "_cott_impl_SimpleTask_priority_level", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.SimpleTask.priority_level")
                _result = await _implementation(self)
            except BaseException as _error:
                self.title = _cott_validate_abi(self.title, str, path="$.title")
                self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
                self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
                self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
                if self.title is not _cott_old_title:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="exceptional-frame", span={"end_byte":1598,"end_column":5,"end_line":68,"start_byte":1496,"start_column":5,"start_line":63}, expected="self.title unchanged", actual="self.title changed")
                if self.urgency is not _cott_old_urgency:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="exceptional-frame", span={"end_byte":1598,"end_column":5,"end_line":68,"start_byte":1496,"start_column":5,"start_line":63}, expected="self.urgency unchanged", actual="self.urgency changed")
                if self.lifecycle is not _cott_old_lifecycle:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="exceptional-frame", span={"end_byte":1598,"end_column":5,"end_line":68,"start_byte":1496,"start_column":5,"start_line":63}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
                if self.completion_count is not _cott_old_completion_count:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="exceptional-frame", span={"end_byte":1598,"end_column":5,"end_line":68,"start_byte":1496,"start_column":5,"start_line":63}, expected="self.completion_count unchanged", actual="self.completion_count changed")
                if not ((len((self).title) > 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1155,"end_column":33,"end_line":47,"start_byte":1127,"start_column":5,"start_line":47}, expected="true", actual="false")
                if not (((self).urgency >= 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1187,"end_column":32,"end_line":48,"start_byte":1160,"start_column":5,"start_line":48}, expected="true", actual="false")
                if not (((self).completion_count >= 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1228,"end_column":41,"end_line":49,"start_byte":1192,"start_column":5,"start_line":49}, expected="true", actual="false")
                if isinstance(_error, _asyncio.CancelledError):
                    raise
                if isinstance(_error, CottContractViolation):
                    if _error.symbol is None or _error.symbol == "_cott_load":
                        _error.symbol = "curriculum.trait_protocol.SimpleTask.priority_level"
                    if _error.span is None:
                        _error.span = {"end_byte":1598,"end_column":5,"end_line":68,"start_byte":1496,"start_column":5,"start_line":63}
                    raise
                if isinstance(_error, SystemExit):
                    raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="implementation-call", span={"end_byte":1598,"end_column":5,"end_line":68,"start_byte":1496,"start_column":5,"start_line":63}, expected="ordinary return", actual="SystemExit") from _error
                if isinstance(_error, Exception):
                    raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="implementation-call", span={"end_byte":1598,"end_column":5,"end_line":68,"start_byte":1496,"start_column":5,"start_line":63}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
                raise
            _result = _cott_validate_abi(_result, I32, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":1598,"end_column":5,"end_line":68,"start_byte":1496,"start_column":5,"start_line":63}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":1598,"end_column":5,"end_line":68,"start_byte":1496,"start_column":5,"start_line":63}, expected="self.urgency unchanged", actual="self.urgency changed")
            if self.lifecycle is not _cott_old_lifecycle:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":1598,"end_column":5,"end_line":68,"start_byte":1496,"start_column":5,"start_line":63}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
            if self.completion_count is not _cott_old_completion_count:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":1598,"end_column":5,"end_line":68,"start_byte":1496,"start_column":5,"start_line":63}, expected="self.completion_count unchanged", actual="self.completion_count changed")
            if not ((_result == (self).urgency)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", clause="ensures:0", phase="ensures", span={"end_byte":1572,"end_column":39,"end_line":64,"start_byte":1542,"start_column":9,"start_line":64}, expected="true", actual="false")
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1155,"end_column":33,"end_line":47,"start_byte":1127,"start_column":5,"start_line":47}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1187,"end_column":32,"end_line":48,"start_byte":1160,"start_column":5,"start_line":48}, expected="true", actual="false")
            if not (((self).completion_count >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1228,"end_column":41,"end_line":49,"start_byte":1192,"start_column":5,"start_line":49}, expected="true", actual="false")
            _result = _cott_wrap_async_protocol(_result, I32, path="$.return", validator=_cott_validate_abi)
            return _result

    async def summary(self: SimpleTask) -> str:
        async with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_lifecycle = self.lifecycle
            _cott_old_completion_count = self.completion_count
            try:
                _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/SimpleTask/summary.py", "32cd3a679cf07989bd53e30b092110359ce4f02e8f8964b3dfd2198134d32c96", "_cott_impl_SimpleTask_summary", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.SimpleTask.summary")
                _result = await _implementation(self)
            except BaseException as _error:
                self.title = _cott_validate_abi(self.title, str, path="$.title")
                self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
                self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
                self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
                if self.title is not _cott_old_title:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="exceptional-frame", span={"end_byte":1496,"end_column":5,"end_line":63,"start_byte":1409,"start_column":5,"start_line":58}, expected="self.title unchanged", actual="self.title changed")
                if self.urgency is not _cott_old_urgency:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="exceptional-frame", span={"end_byte":1496,"end_column":5,"end_line":63,"start_byte":1409,"start_column":5,"start_line":58}, expected="self.urgency unchanged", actual="self.urgency changed")
                if self.lifecycle is not _cott_old_lifecycle:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="exceptional-frame", span={"end_byte":1496,"end_column":5,"end_line":63,"start_byte":1409,"start_column":5,"start_line":58}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
                if self.completion_count is not _cott_old_completion_count:
                    raise CottContractViolation("exceptional frame clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="exceptional-frame", span={"end_byte":1496,"end_column":5,"end_line":63,"start_byte":1409,"start_column":5,"start_line":58}, expected="self.completion_count unchanged", actual="self.completion_count changed")
                if not ((len((self).title) > 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1155,"end_column":33,"end_line":47,"start_byte":1127,"start_column":5,"start_line":47}, expected="true", actual="false")
                if not (((self).urgency >= 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1187,"end_column":32,"end_line":48,"start_byte":1160,"start_column":5,"start_line":48}, expected="true", actual="false")
                if not (((self).completion_count >= 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1228,"end_column":41,"end_line":49,"start_byte":1192,"start_column":5,"start_line":49}, expected="true", actual="false")
                if isinstance(_error, _asyncio.CancelledError):
                    raise
                if isinstance(_error, CottContractViolation):
                    if _error.symbol is None or _error.symbol == "_cott_load":
                        _error.symbol = "curriculum.trait_protocol.SimpleTask.summary"
                    if _error.span is None:
                        _error.span = {"end_byte":1496,"end_column":5,"end_line":63,"start_byte":1409,"start_column":5,"start_line":58}
                    raise
                if isinstance(_error, SystemExit):
                    raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="implementation-call", span={"end_byte":1496,"end_column":5,"end_line":63,"start_byte":1409,"start_column":5,"start_line":58}, expected="ordinary return", actual="SystemExit") from _error
                if isinstance(_error, Exception):
                    raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="implementation-call", span={"end_byte":1496,"end_column":5,"end_line":63,"start_byte":1409,"start_column":5,"start_line":58}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
                raise
            _result = _cott_validate_abi(_result, str, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            self.completion_count = _cott_validate_abi(self.completion_count, I32, path="$.completion_count")
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":1496,"end_column":5,"end_line":63,"start_byte":1409,"start_column":5,"start_line":58}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":1496,"end_column":5,"end_line":63,"start_byte":1409,"start_column":5,"start_line":58}, expected="self.urgency unchanged", actual="self.urgency changed")
            if self.lifecycle is not _cott_old_lifecycle:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":1496,"end_column":5,"end_line":63,"start_byte":1409,"start_column":5,"start_line":58}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
            if self.completion_count is not _cott_old_completion_count:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":1496,"end_column":5,"end_line":63,"start_byte":1409,"start_column":5,"start_line":58}, expected="self.completion_count unchanged", actual="self.completion_count changed")
            if not ((len(_result) > 0)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", clause="ensures:0", phase="ensures", span={"end_byte":1470,"end_column":31,"end_line":59,"start_byte":1448,"start_column":9,"start_line":59}, expected="true", actual="false")
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1155,"end_column":33,"end_line":47,"start_byte":1127,"start_column":5,"start_line":47}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1187,"end_column":32,"end_line":48,"start_byte":1160,"start_column":5,"start_line":48}, expected="true", actual="false")
            if not (((self).completion_count >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1228,"end_column":41,"end_line":49,"start_byte":1192,"start_column":5,"start_line":49}, expected="true", actual="false")
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
                if not ((len((self).title) > 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1155,"end_column":33,"end_line":47,"start_byte":1127,"start_column":5,"start_line":47}, expected="true", actual="false")
                if not (((self).urgency >= 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1187,"end_column":32,"end_line":48,"start_byte":1160,"start_column":5,"start_line":48}, expected="true", actual="false")
                if not (((self).completion_count >= 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1228,"end_column":41,"end_line":49,"start_byte":1192,"start_column":5,"start_line":49}, expected="true", actual="false")
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
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1155,"end_column":33,"end_line":47,"start_byte":1127,"start_column":5,"start_line":47}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1187,"end_column":32,"end_line":48,"start_byte":1160,"start_column":5,"start_line":48}, expected="true", actual="false")
            if not (((self).completion_count >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1228,"end_column":41,"end_line":49,"start_byte":1192,"start_column":5,"start_line":49}, expected="true", actual="false")
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
                if not ((len((self).title) > 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1155,"end_column":33,"end_line":47,"start_byte":1127,"start_column":5,"start_line":47}, expected="true", actual="false")
                if not (((self).urgency >= 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1187,"end_column":32,"end_line":48,"start_byte":1160,"start_column":5,"start_line":48}, expected="true", actual="false")
                if not (((self).completion_count >= 0)):
                    raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1228,"end_column":41,"end_line":49,"start_byte":1192,"start_column":5,"start_line":49}, expected="true", actual="false")
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
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1155,"end_column":33,"end_line":47,"start_byte":1127,"start_column":5,"start_line":47}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1187,"end_column":32,"end_line":48,"start_byte":1160,"start_column":5,"start_line":48}, expected="true", actual="false")
            if not (((self).completion_count >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:2", phase="invariant", span={"end_byte":1228,"end_column":41,"end_line":49,"start_byte":1192,"start_column":5,"start_line":49}, expected="true", actual="false")
            _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
            return _result

__all__ = ["Completable", "Prioritizable", "SimpleTask", "Summarizable", "TaskLifecycle", "TaskLifecycle_Completed", "TaskLifecycle_Pending", "TaskView", "default_category", "inspect_dyn", "specialized_display", "task_factory"]
