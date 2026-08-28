from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.trait_protocol_types import Completable, Prioritizable, Summarizable, TaskLifecycle, TaskLifecycle_Completed, TaskLifecycle_Pending, _cott__cott_inspect_task_T_Bounds, _cott_curriculum_trait_protocol_Summarizable_curriculum_trait_protocol_Summarizable_Summary

_cott_format_summary_T = TypeVar("_cott_format_summary_T", bound=Summarizable)
_cott_inspect_task_T = TypeVar("_cott_inspect_task_T", bound=_cott__cott_inspect_task_T_Bounds)

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
            _error.span = {"end_byte":415,"end_column":1,"end_line":22,"start_byte":224,"start_column":1,"start_line":13}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.format_summary", phase="implementation-call", span={"end_byte":415,"end_column":1,"end_line":22,"start_byte":224,"start_column":1,"start_line":13}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.format_summary", phase="implementation-call", span={"end_byte":415,"end_column":1,"end_line":22,"start_byte":224,"start_column":1,"start_line":13}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) >= 0)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.format_summary", clause="ensures:1", phase="ensures", span={"end_byte":397,"end_column":28,"end_line":18,"start_byte":374,"start_column":5,"start_line":18}, expected="true", actual="false")
    return _result

def inspect_task(item: _cott_inspect_task_T) -> str:
    """Inspect an item requiring both {Summarizable} and {Prioritizable} trait bounds."""
    item = _cott_validate_abi(item, _cott_inspect_task_T, path="$.item")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/inspect_task.py", "a62575d547b8ce99de539c78514bf41b84e41c64b6dd7950670256eeee235fbe", "inspect_task", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.inspect_task")
        _result = _implementation(item)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.trait_protocol.inspect_task"
        if _error.span is None:
            _error.span = {"end_byte":630,"end_column":1,"end_line":31,"start_byte":415,"start_column":1,"start_line":22}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.inspect_task", phase="implementation-call", span={"end_byte":630,"end_column":1,"end_line":31,"start_byte":415,"start_column":1,"start_line":22}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.inspect_task", phase="implementation-call", span={"end_byte":630,"end_column":1,"end_line":31,"start_byte":415,"start_column":1,"start_line":22}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) > 0)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.inspect_task", clause="ensures:1", phase="ensures", span={"end_byte":612,"end_column":27,"end_line":27,"start_byte":590,"start_column":5,"start_line":27}, expected="true", actual="false")
    return _result

@final
class SimpleTask:
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
            raise CottContractViolation("requires clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="requires:0", phase="requires", span={"end_byte":1076,"end_column":31,"end_line":49,"start_byte":1054,"start_column":9,"start_line":49}, expected="true", actual="false")
        if not ((urgency >= 0)):
            raise CottContractViolation("requires clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="requires:1", phase="requires", span={"end_byte":1106,"end_column":30,"end_line":50,"start_byte":1085,"start_column":9,"start_line":50}, expected="true", actual="false")
        self.title = _cott_validate_abi(title, str, path="$.title")
        self.urgency = _cott_validate_abi(urgency, I32, path="$.urgency")
        self.lifecycle = _cott_validate_abi(TaskLifecycle_Pending(), TaskLifecycle, path="$.lifecycle")
        self._cott_lock = _threading.RLock()
        if not (((self).title == title)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="ensures:2", phase="ensures", span={"end_byte":1143,"end_column":36,"end_line":52,"start_byte":1116,"start_column":9,"start_line":52}, expected="true", actual="false")
        if not (((self).urgency == urgency)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="ensures:3", phase="ensures", span={"end_byte":1183,"end_column":40,"end_line":53,"start_byte":1152,"start_column":9,"start_line":53}, expected="true", actual="false")
        if not ((len((self).title) > 0)):
            raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":976,"end_column":33,"end_line":45,"start_byte":948,"start_column":5,"start_line":45}, expected="true", actual="false")
        if not (((self).urgency >= 0)):
            raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1008,"end_column":32,"end_line":46,"start_byte":981,"start_column":5,"start_line":46}, expected="true", actual="false")

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
                    _error.span = {"end_byte":1270,"end_column":5,"end_line":60,"start_byte":1189,"start_column":5,"start_line":55}
                raise
            except SystemExit as _error:
                raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="implementation-call", span={"end_byte":1270,"end_column":5,"end_line":60,"start_byte":1189,"start_column":5,"start_line":55}, expected="ordinary return", actual="SystemExit") from _error
            except Exception as _error:
                raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="implementation-call", span={"end_byte":1270,"end_column":5,"end_line":60,"start_byte":1189,"start_column":5,"start_line":55}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
            _result = _cott_validate_abi(_result, str, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":1270,"end_column":5,"end_line":60,"start_byte":1189,"start_column":5,"start_line":55}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":1270,"end_column":5,"end_line":60,"start_byte":1189,"start_column":5,"start_line":55}, expected="self.urgency unchanged", actual="self.urgency changed")
            if self.lifecycle is not _cott_old_lifecycle:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":1270,"end_column":5,"end_line":60,"start_byte":1189,"start_column":5,"start_line":55}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
            if not ((len(_result) > 0)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", clause="ensures:0", phase="ensures", span={"end_byte":1244,"end_column":31,"end_line":56,"start_byte":1222,"start_column":9,"start_line":56}, expected="true", actual="false")
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":976,"end_column":33,"end_line":45,"start_byte":948,"start_column":5,"start_line":45}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1008,"end_column":32,"end_line":46,"start_byte":981,"start_column":5,"start_line":46}, expected="true", actual="false")
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
                    _error.span = {"end_byte":1366,"end_column":5,"end_line":65,"start_byte":1270,"start_column":5,"start_line":60}
                raise
            except SystemExit as _error:
                raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="implementation-call", span={"end_byte":1366,"end_column":5,"end_line":65,"start_byte":1270,"start_column":5,"start_line":60}, expected="ordinary return", actual="SystemExit") from _error
            except Exception as _error:
                raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="implementation-call", span={"end_byte":1366,"end_column":5,"end_line":65,"start_byte":1270,"start_column":5,"start_line":60}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
            _result = _cott_validate_abi(_result, I32, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":1366,"end_column":5,"end_line":65,"start_byte":1270,"start_column":5,"start_line":60}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":1366,"end_column":5,"end_line":65,"start_byte":1270,"start_column":5,"start_line":60}, expected="self.urgency unchanged", actual="self.urgency changed")
            if self.lifecycle is not _cott_old_lifecycle:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":1366,"end_column":5,"end_line":65,"start_byte":1270,"start_column":5,"start_line":60}, expected="self.lifecycle unchanged", actual="self.lifecycle changed")
            if not ((_result == (self).urgency)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", clause="ensures:0", phase="ensures", span={"end_byte":1340,"end_column":39,"end_line":61,"start_byte":1310,"start_column":9,"start_line":61}, expected="true", actual="false")
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":976,"end_column":33,"end_line":45,"start_byte":948,"start_column":5,"start_line":45}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1008,"end_column":32,"end_line":46,"start_byte":981,"start_column":5,"start_line":46}, expected="true", actual="false")
            return _result

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
                    _error.span = {"end_byte":1510,"end_column":1,"end_line":69,"start_byte":1366,"start_column":5,"start_line":65}
                raise
            except SystemExit as _error:
                raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="implementation-call", span={"end_byte":1510,"end_column":1,"end_line":69,"start_byte":1366,"start_column":5,"start_line":65}, expected="ordinary return", actual="SystemExit") from _error
            except Exception as _error:
                raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="implementation-call", span={"end_byte":1510,"end_column":1,"end_line":69,"start_byte":1366,"start_column":5,"start_line":65}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
            _result = _cott_validate_abi(_result, bool, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.lifecycle = _cott_validate_abi(self.lifecycle, TaskLifecycle, path="$.lifecycle")
            if _cott_old_lifecycle is not TaskLifecycle_Pending():
                raise CottContractViolation("resource transition source failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="transitions", span={"end_byte":1510,"end_column":1,"end_line":69,"start_byte":1366,"start_column":5,"start_line":65}, expected="self.lifecycle is TaskLifecycle_Pending", actual=repr(_cott_old_lifecycle))
            if self.lifecycle is not TaskLifecycle_Completed():
                raise CottContractViolation("resource transition target failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="transitions", span={"end_byte":1510,"end_column":1,"end_line":69,"start_byte":1366,"start_column":5,"start_line":65}, expected="self.lifecycle is TaskLifecycle_Completed", actual=repr(self.lifecycle))
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="modifies", span={"end_byte":1510,"end_column":1,"end_line":69,"start_byte":1366,"start_column":5,"start_line":65}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="modifies", span={"end_byte":1510,"end_column":1,"end_line":69,"start_byte":1366,"start_column":5,"start_line":65}, expected="self.urgency unchanged", actual="self.urgency changed")
            if not ((_result == True)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", clause="ensures:1", phase="ensures", span={"end_byte":1509,"end_column":31,"end_line":68,"start_byte":1487,"start_column":9,"start_line":68}, expected="true", actual="false")
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":976,"end_column":33,"end_line":45,"start_byte":948,"start_column":5,"start_line":45}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":1008,"end_column":32,"end_line":46,"start_byte":981,"start_column":5,"start_line":46}, expected="true", actual="false")
            return _result

__all__ = ["Completable", "Prioritizable", "SimpleTask", "Summarizable", "TaskLifecycle", "TaskLifecycle_Completed", "TaskLifecycle_Pending", "format_summary", "inspect_task"]
