from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.trait_protocol_types import Completable, Prioritizable, Summarizable, TaskLifecycle, TaskLifecycle_Completed, TaskLifecycle_Pending, TaskView, _cott_curriculum_trait_protocol_Summarizable_Summary_91a0038fc149a52d660ec2d4c914e0f201ef340095a79ffc2c9cd89ad6d2311f, _cott_curriculum_trait_protocol_Summarizable_curriculum_trait_protocol_Summarizable_Summary, _cott_curriculum_trait_protocol_TaskView_curriculum_trait_protocol_Summarizable_Summary

_cott_format_summary_T = TypeVar("_cott_format_summary_T", bound=Summarizable)
_cott_inspect_task_T = TypeVar("_cott_inspect_task_T", bound=TaskView)

def format_summary(item: _cott_format_summary_T) -> str:
    """Format the summary string from any item implementing {Summarizable}."""
    item = _cott_validate_abi(item, _cott_format_summary_T, path="$.item")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/format_summary.py", "71428b73a1d0ba4a5cd902b5bb784aba4d2a86a720150ad42c5db188b94dc66e", "format_summary", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.format_summary")
        _result = _implementation(item)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.trait_protocol.format_summary"
        if _error.span is None:
            _error.span = {"end_byte":465,"end_column":1,"end_line":24,"start_byte":274,"start_column":1,"start_line":15}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.format_summary", phase="implementation-call", span={"end_byte":465,"end_column":1,"end_line":24,"start_byte":274,"start_column":1,"start_line":15}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.format_summary", phase="implementation-call", span={"end_byte":465,"end_column":1,"end_line":24,"start_byte":274,"start_column":1,"start_line":15}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) >= 0)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.format_summary", clause="ensures:1", phase="ensures", span={"end_byte":447,"end_column":28,"end_line":20,"start_byte":424,"start_column":5,"start_line":20}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def inspect_task(item: _cott_inspect_task_T) -> str:
    """Inspect an item implementing {TaskView}."""
    item = _cott_validate_abi(item, _cott_inspect_task_T, path="$.item")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/inspect_task.py", "b19c28aa7a30faf056d522d3301677d8e4141a3d0d90af38c7b91a0ece99b24a", "inspect_task", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.inspect_task")
        _result = _implementation(item)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.trait_protocol.inspect_task"
        if _error.span is None:
            _error.span = {"end_byte":621,"end_column":1,"end_line":33,"start_byte":465,"start_column":1,"start_line":24}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.inspect_task", phase="implementation-call", span={"end_byte":621,"end_column":1,"end_line":33,"start_byte":465,"start_column":1,"start_line":24}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.inspect_task", phase="implementation-call", span={"end_byte":621,"end_column":1,"end_line":33,"start_byte":465,"start_column":1,"start_line":24}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) > 0)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.inspect_task", clause="ensures:1", phase="ensures", span={"end_byte":603,"end_column":27,"end_line":29,"start_byte":581,"start_column":5,"start_line":29}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def inspect_dyn(item: Dyn[TaskView]) -> str:
    item = _cott_validate_abi(item, Dyn[TaskView], path="$.item")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/inspect_dyn.py", "1d063ed8744dc4a59599f14e89ab99026650a9938f2129da66500a055f8cdc3a", "inspect_dyn", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.inspect_dyn")
        _result = _implementation(item)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.trait_protocol.inspect_dyn"
        if _error.span is None:
            _error.span = {"end_byte":681,"end_column":1,"end_line":36,"start_byte":621,"start_column":1,"start_line":33}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.inspect_dyn", phase="implementation-call", span={"end_byte":681,"end_column":1,"end_line":36,"start_byte":621,"start_column":1,"start_line":33}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.inspect_dyn", phase="implementation-call", span={"end_byte":681,"end_column":1,"end_line":36,"start_byte":621,"start_column":1,"start_line":33}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

@final
class SimpleTask:
    _cott_traits = (Completable, Prioritizable, Summarizable, TaskView,)
    _cott_trait_specs = (Completable, Prioritizable, Summarizable, TaskView,)
    title: str
    urgency: I32
    lifecycle: TaskLifecycle
    __slots__ = ("title", "urgency", "lifecycle", "_cott_lock",)

    def __init_subclass__(cls, **_kwargs: object) -> None:
        raise TypeError("SimpleTask is final")

    def __init__(self, title: str, urgency: I32) -> None:
        title = _cott_validate_abi(title, str, path="$.title")
        urgency = _cott_validate_abi(urgency, I32, path="$.urgency")
        if not ((len(title) > 0)):
            raise CottContractViolation("requires clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="requires:0", phase="requires", span={"end_byte":1107,"end_column":31,"end_line":54,"start_byte":1085,"start_column":9,"start_line":54}, expected="true", actual="false")
        if not ((urgency >= 0)):
            raise CottContractViolation("requires clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="requires:1", phase="requires", span={"end_byte":1137,"end_column":30,"end_line":55,"start_byte":1116,"start_column":9,"start_line":55}, expected="true", actual="false")
        self.title = _cott_validate_abi(title, str, path="$.title")
        self.urgency = _cott_validate_abi(urgency, I32, path="$.urgency")
        self.lifecycle = _cott_validate_abi(TaskLifecycle_Pending(), TaskLifecycle, path="$.lifecycle")
        self._cott_lock = _threading.RLock()
        if not (((self).title == title)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="ensures:2", phase="ensures", span={"end_byte":1174,"end_column":36,"end_line":57,"start_byte":1147,"start_column":9,"start_line":57}, expected="true", actual="false")
        if not (((self).urgency == urgency)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="ensures:3", phase="ensures", span={"end_byte":1214,"end_column":40,"end_line":58,"start_byte":1183,"start_column":9,"start_line":58}, expected="true", actual="false")
        if not ((len((self).title) > 0)):
            raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1007,"end_column":33,"end_line":50,"start_byte":979,"start_column":5,"start_line":50}, expected="true", actual="false")
        if not (((self).urgency >= 0)):
            raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1039,"end_column":32,"end_line":51,"start_byte":1012,"start_column":5,"start_line":51}, expected="true", actual="false")

    def complete(self: SimpleTask) -> bool:
        with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_lifecycle = self.lifecycle
            try:
                _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/SimpleTask/complete.py", "8d8670d9dcc6d1620876221c534dadafae4063a6546c350c4240233de04dad2d", "_cott_impl_SimpleTask_complete", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.SimpleTask.complete")
                _result = _implementation(self)
            except CottContractViolation as _error:
                if _error.symbol is None or _error.symbol == "_cott_load":
                    _error.symbol = "curriculum.trait_protocol.SimpleTask.complete"
                if _error.span is None:
                    _error.span = {"end_byte":1541,"end_column":1,"end_line":74,"start_byte":1397,"start_column":5,"start_line":70}
                raise
            except SystemExit as _error:
                raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="implementation-call", span={"end_byte":1541,"end_column":1,"end_line":74,"start_byte":1397,"start_column":5,"start_line":70}, expected="ordinary return", actual="SystemExit") from _error
            except Exception as _error:
                raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="implementation-call", span={"end_byte":1541,"end_column":1,"end_line":74,"start_byte":1397,"start_column":5,"start_line":70}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
            _result = _cott_validate_abi(_result, bool, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            if _cott_old_lifecycle is not TaskLifecycle_Pending():
                raise CottContractViolation("resource transition source failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="transitions", span={"end_byte":1541,"end_column":1,"end_line":74,"start_byte":1397,"start_column":5,"start_line":70}, expected="self.lifecycle is TaskLifecycle_Pending", actual=repr(_cott_old_lifecycle))
            if self.lifecycle is not TaskLifecycle_Completed():
                raise CottContractViolation("resource transition target failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="transitions", span={"end_byte":1541,"end_column":1,"end_line":74,"start_byte":1397,"start_column":5,"start_line":70}, expected="self.lifecycle is TaskLifecycle_Completed", actual=repr(self.lifecycle))
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="modifies", span={"end_byte":1541,"end_column":1,"end_line":74,"start_byte":1397,"start_column":5,"start_line":70}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="modifies", span={"end_byte":1541,"end_column":1,"end_line":74,"start_byte":1397,"start_column":5,"start_line":70}, expected="self.urgency unchanged", actual="self.urgency changed")
            if not ((_result == True)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", clause="ensures:1", phase="ensures", span={"end_byte":1540,"end_column":31,"end_line":73,"start_byte":1518,"start_column":9,"start_line":73}, expected="true", actual="false")
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1007,"end_column":33,"end_line":50,"start_byte":979,"start_column":5,"start_line":50}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1039,"end_column":32,"end_line":51,"start_byte":1012,"start_column":5,"start_line":51}, expected="true", actual="false")
            _result = _cott_wrap_async_protocol(_result, bool, path="$.return", validator=_cott_validate_abi)
            return _result

    def priority_level(self: SimpleTask) -> I32:
        with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_lifecycle = self.lifecycle
            try:
                _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/SimpleTask/priority_level.py", "92bf43065b798d4d42e429f7acee7e21a80dbc4401a2f8af266a983290c53e5a", "_cott_impl_SimpleTask_priority_level", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.SimpleTask.priority_level")
                _result = _implementation(self)
            except CottContractViolation as _error:
                if _error.symbol is None or _error.symbol == "_cott_load":
                    _error.symbol = "curriculum.trait_protocol.SimpleTask.priority_level"
                if _error.span is None:
                    _error.span = {"end_byte":1397,"end_column":5,"end_line":70,"start_byte":1301,"start_column":5,"start_line":65}
                raise
            except SystemExit as _error:
                raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="implementation-call", span={"end_byte":1397,"end_column":5,"end_line":70,"start_byte":1301,"start_column":5,"start_line":65}, expected="ordinary return", actual="SystemExit") from _error
            except Exception as _error:
                raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="implementation-call", span={"end_byte":1397,"end_column":5,"end_line":70,"start_byte":1301,"start_column":5,"start_line":65}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
            _result = _cott_validate_abi(_result, I32, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":1397,"end_column":5,"end_line":70,"start_byte":1301,"start_column":5,"start_line":65}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":1397,"end_column":5,"end_line":70,"start_byte":1301,"start_column":5,"start_line":65}, expected="self.urgency unchanged", actual="self.urgency changed")
            if self.lifecycle is not _cott_old_lifecycle:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":1397,"end_column":5,"end_line":70,"start_byte":1301,"start_column":5,"start_line":65}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
            if not ((_result == (self).urgency)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", clause="ensures:0", phase="ensures", span={"end_byte":1371,"end_column":39,"end_line":66,"start_byte":1341,"start_column":9,"start_line":66}, expected="true", actual="false")
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1007,"end_column":33,"end_line":50,"start_byte":979,"start_column":5,"start_line":50}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1039,"end_column":32,"end_line":51,"start_byte":1012,"start_column":5,"start_line":51}, expected="true", actual="false")
            _result = _cott_wrap_async_protocol(_result, I32, path="$.return", validator=_cott_validate_abi)
            return _result

    def summary(self: SimpleTask) -> str:
        with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_lifecycle = self.lifecycle
            try:
                _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/SimpleTask/summary.py", "69f34fe32008918eea69c5e761cf85f2fc66436d2aba6c6078ae33f22b0d47b8", "_cott_impl_SimpleTask_summary", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.SimpleTask.summary")
                _result = _implementation(self)
            except CottContractViolation as _error:
                if _error.symbol is None or _error.symbol == "_cott_load":
                    _error.symbol = "curriculum.trait_protocol.SimpleTask.summary"
                if _error.span is None:
                    _error.span = {"end_byte":1301,"end_column":5,"end_line":65,"start_byte":1220,"start_column":5,"start_line":60}
                raise
            except SystemExit as _error:
                raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="implementation-call", span={"end_byte":1301,"end_column":5,"end_line":65,"start_byte":1220,"start_column":5,"start_line":60}, expected="ordinary return", actual="SystemExit") from _error
            except Exception as _error:
                raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="implementation-call", span={"end_byte":1301,"end_column":5,"end_line":65,"start_byte":1220,"start_column":5,"start_line":60}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
            _result = _cott_validate_abi(_result, str, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":1301,"end_column":5,"end_line":65,"start_byte":1220,"start_column":5,"start_line":60}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":1301,"end_column":5,"end_line":65,"start_byte":1220,"start_column":5,"start_line":60}, expected="self.urgency unchanged", actual="self.urgency changed")
            if self.lifecycle is not _cott_old_lifecycle:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":1301,"end_column":5,"end_line":65,"start_byte":1220,"start_column":5,"start_line":60}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
            if not ((len(_result) > 0)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", clause="ensures:0", phase="ensures", span={"end_byte":1275,"end_column":31,"end_line":61,"start_byte":1253,"start_column":9,"start_line":61}, expected="true", actual="false")
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":1007,"end_column":33,"end_line":50,"start_byte":979,"start_column":5,"start_line":50}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1039,"end_column":32,"end_line":51,"start_byte":1012,"start_column":5,"start_line":51}, expected="true", actual="false")
            _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
            return _result

__all__ = ["Completable", "Prioritizable", "SimpleTask", "Summarizable", "TaskLifecycle", "TaskLifecycle_Completed", "TaskLifecycle_Pending", "TaskView", "format_summary", "inspect_dyn", "inspect_task"]
