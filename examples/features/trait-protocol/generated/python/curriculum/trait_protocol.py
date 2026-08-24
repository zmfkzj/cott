from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.trait_protocol_types import Completable, Prioritizable, Summarizable, _cott__cott_inspect_task_T_Bounds

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
            _error.span = {"end_byte":381,"end_column":1,"end_line":21,"start_byte":190,"start_column":1,"start_line":12}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.format_summary", phase="implementation-call", span={"end_byte":381,"end_column":1,"end_line":21,"start_byte":190,"start_column":1,"start_line":12}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.format_summary", phase="implementation-call", span={"end_byte":381,"end_column":1,"end_line":21,"start_byte":190,"start_column":1,"start_line":12}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) >= 0)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.format_summary", clause="ensures:1", phase="ensures", span={"end_byte":363,"end_column":28,"end_line":17,"start_byte":340,"start_column":5,"start_line":17}, expected="true", actual="false")
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
            _error.span = {"end_byte":596,"end_column":1,"end_line":30,"start_byte":381,"start_column":1,"start_line":21}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.inspect_task", phase="implementation-call", span={"end_byte":596,"end_column":1,"end_line":30,"start_byte":381,"start_column":1,"start_line":21}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.inspect_task", phase="implementation-call", span={"end_byte":596,"end_column":1,"end_line":30,"start_byte":381,"start_column":1,"start_line":21}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not ((len(_result) > 0)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.inspect_task", clause="ensures:1", phase="ensures", span={"end_byte":578,"end_column":27,"end_line":26,"start_byte":556,"start_column":5,"start_line":26}, expected="true", actual="false")
    return _result

@final
class SimpleTask:
    title: str
    urgency: I32
    completed: bool
    __slots__ = ("title", "urgency", "completed", "_cott_lock",)

    def __init_subclass__(cls, **_kwargs: object) -> None:
        raise TypeError("SimpleTask is final")

    def __init__(self, title: str, urgency: I32) -> None:
        title = _cott_validate_abi(title, str, path="$.title")
        urgency = _cott_validate_abi(urgency, I32, path="$.urgency")
        if not ((len(title) > 0)):
            raise CottContractViolation("requires clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="requires:0", phase="requires", span={"end_byte":876,"end_column":31,"end_line":40,"start_byte":854,"start_column":9,"start_line":40}, expected="true", actual="false")
        if not ((urgency >= 0)):
            raise CottContractViolation("requires clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="requires:1", phase="requires", span={"end_byte":906,"end_column":30,"end_line":41,"start_byte":885,"start_column":9,"start_line":41}, expected="true", actual="false")
        self.title = _cott_validate_abi(title, str, path="$.title")
        self.urgency = _cott_validate_abi(urgency, I32, path="$.urgency")
        self.completed = _cott_validate_abi(False, bool, path="$.completed")
        self._cott_lock = _threading.RLock()
        if not (((self).title == title)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="ensures:2", phase="ensures", span={"end_byte":943,"end_column":36,"end_line":43,"start_byte":916,"start_column":9,"start_line":43}, expected="true", actual="false")
        if not (((self).urgency == urgency)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="ensures:3", phase="ensures", span={"end_byte":983,"end_column":40,"end_line":44,"start_byte":952,"start_column":9,"start_line":44}, expected="true", actual="false")
        if not (((self).completed == False)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask", clause="ensures:4", phase="ensures", span={"end_byte":1023,"end_column":40,"end_line":45,"start_byte":992,"start_column":9,"start_line":45}, expected="true", actual="false")
        if not ((len((self).title) > 0)):
            raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":776,"end_column":33,"end_line":36,"start_byte":748,"start_column":5,"start_line":36}, expected="true", actual="false")
        if not (((self).urgency >= 0)):
            raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":808,"end_column":32,"end_line":37,"start_byte":781,"start_column":5,"start_line":37}, expected="true", actual="false")

    def summary(self: SimpleTask) -> str:
        with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_completed = self.completed
            try:
                _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/SimpleTask/summary.py", "69f34fe32008918eea69c5e761cf85f2fc66436d2aba6c6078ae33f22b0d47b8", "_cott_impl_SimpleTask_summary", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.SimpleTask.summary")
                _result = _implementation(self)
            except CottContractViolation as _error:
                if _error.symbol is None or _error.symbol == "_cott_load":
                    _error.symbol = "curriculum.trait_protocol.SimpleTask.summary"
                if _error.span is None:
                    _error.span = {"end_byte":1110,"end_column":5,"end_line":52,"start_byte":1029,"start_column":5,"start_line":47}
                raise
            except SystemExit as _error:
                raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="implementation-call", span={"end_byte":1110,"end_column":5,"end_line":52,"start_byte":1029,"start_column":5,"start_line":47}, expected="ordinary return", actual="SystemExit") from _error
            except Exception as _error:
                raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="implementation-call", span={"end_byte":1110,"end_column":5,"end_line":52,"start_byte":1029,"start_column":5,"start_line":47}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
            _result = _cott_validate_abi(_result, str, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.completed = _cott_validate_abi(self.completed, bool, path="$.completed")
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":1110,"end_column":5,"end_line":52,"start_byte":1029,"start_column":5,"start_line":47}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":1110,"end_column":5,"end_line":52,"start_byte":1029,"start_column":5,"start_line":47}, expected="self.urgency unchanged", actual="self.urgency changed")
            if self.completed is not _cott_old_completed:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", phase="modifies", span={"end_byte":1110,"end_column":5,"end_line":52,"start_byte":1029,"start_column":5,"start_line":47}, expected="self.completed unchanged", actual="self.completed changed")
            if not ((len(_result) > 0)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.summary", clause="ensures:0", phase="ensures", span={"end_byte":1084,"end_column":31,"end_line":48,"start_byte":1062,"start_column":9,"start_line":48}, expected="true", actual="false")
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":776,"end_column":33,"end_line":36,"start_byte":748,"start_column":5,"start_line":36}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":808,"end_column":32,"end_line":37,"start_byte":781,"start_column":5,"start_line":37}, expected="true", actual="false")
            return _result

    def priority_level(self: SimpleTask) -> I32:
        with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_completed = self.completed
            try:
                _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/SimpleTask/priority_level.py", "92bf43065b798d4d42e429f7acee7e21a80dbc4401a2f8af266a983290c53e5a", "_cott_impl_SimpleTask_priority_level", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.SimpleTask.priority_level")
                _result = _implementation(self)
            except CottContractViolation as _error:
                if _error.symbol is None or _error.symbol == "_cott_load":
                    _error.symbol = "curriculum.trait_protocol.SimpleTask.priority_level"
                if _error.span is None:
                    _error.span = {"end_byte":1206,"end_column":5,"end_line":57,"start_byte":1110,"start_column":5,"start_line":52}
                raise
            except SystemExit as _error:
                raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="implementation-call", span={"end_byte":1206,"end_column":5,"end_line":57,"start_byte":1110,"start_column":5,"start_line":52}, expected="ordinary return", actual="SystemExit") from _error
            except Exception as _error:
                raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="implementation-call", span={"end_byte":1206,"end_column":5,"end_line":57,"start_byte":1110,"start_column":5,"start_line":52}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
            _result = _cott_validate_abi(_result, I32, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.completed = _cott_validate_abi(self.completed, bool, path="$.completed")
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":1206,"end_column":5,"end_line":57,"start_byte":1110,"start_column":5,"start_line":52}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":1206,"end_column":5,"end_line":57,"start_byte":1110,"start_column":5,"start_line":52}, expected="self.urgency unchanged", actual="self.urgency changed")
            if self.completed is not _cott_old_completed:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", phase="modifies", span={"end_byte":1206,"end_column":5,"end_line":57,"start_byte":1110,"start_column":5,"start_line":52}, expected="self.completed unchanged", actual="self.completed changed")
            if not ((_result == (self).urgency)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.priority_level", clause="ensures:0", phase="ensures", span={"end_byte":1180,"end_column":39,"end_line":53,"start_byte":1150,"start_column":9,"start_line":53}, expected="true", actual="false")
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":776,"end_column":33,"end_line":36,"start_byte":748,"start_column":5,"start_line":36}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":808,"end_column":32,"end_line":37,"start_byte":781,"start_column":5,"start_line":37}, expected="true", actual="false")
            return _result

    def complete(self: SimpleTask) -> bool:
        with self._cott_lock:
            _cott_old_title = self.title
            _cott_old_urgency = self.urgency
            _cott_old_completed = self.completed
            if not (((self).completed == False)):
                raise CottContractViolation("requires clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", clause="requires:0", phase="requires", span={"end_byte":1273,"end_column":41,"end_line":58,"start_byte":1241,"start_column":9,"start_line":58}, expected="true", actual="false")
            try:
                _implementation = _cott_load("_cott_impl/curriculum/trait_protocol/SimpleTask/complete.py", "dbb32a20790deae0debc19ef035a845ce417abd659e507738a6f8b543d9a05ac", "_cott_impl_SimpleTask_complete", expected_project_name="trait-protocol", expected_cott_symbol="curriculum.trait_protocol.SimpleTask.complete")
                _result = _implementation(self)
            except CottContractViolation as _error:
                if _error.symbol is None or _error.symbol == "_cott_load":
                    _error.symbol = "curriculum.trait_protocol.SimpleTask.complete"
                if _error.span is None:
                    _error.span = {"end_byte":1453,"end_column":1,"end_line":67,"start_byte":1206,"start_column":5,"start_line":57}
                raise
            except SystemExit as _error:
                raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="implementation-call", span={"end_byte":1453,"end_column":1,"end_line":67,"start_byte":1206,"start_column":5,"start_line":57}, expected="ordinary return", actual="SystemExit") from _error
            except Exception as _error:
                raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="implementation-call", span={"end_byte":1453,"end_column":1,"end_line":67,"start_byte":1206,"start_column":5,"start_line":57}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
            _result = _cott_validate_abi(_result, bool, path="$.return")
            self.title = _cott_validate_abi(self.title, str, path="$.title")
            self.urgency = _cott_validate_abi(self.urgency, I32, path="$.urgency")
            self.completed = _cott_validate_abi(self.completed, bool, path="$.completed")
            if self.title is not _cott_old_title:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="modifies", span={"end_byte":1453,"end_column":1,"end_line":67,"start_byte":1206,"start_column":5,"start_line":57}, expected="self.title unchanged", actual="self.title changed")
            if self.urgency is not _cott_old_urgency:
                raise CottContractViolation("modifies clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", phase="modifies", span={"end_byte":1453,"end_column":1,"end_line":67,"start_byte":1206,"start_column":5,"start_line":57}, expected="self.urgency unchanged", actual="self.urgency changed")
            if not ((_cott_old_completed == False)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", clause="ensures:2", phase="ensures", span={"end_byte":1352,"end_column":45,"end_line":62,"start_byte":1316,"start_column":9,"start_line":62}, expected="true", actual="false")
            if not (((self).completed == True)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", clause="ensures:3", phase="ensures", span={"end_byte":1391,"end_column":39,"end_line":63,"start_byte":1361,"start_column":9,"start_line":63}, expected="true", actual="false")
            if not ((_result == (self).completed)):
                raise CottContractViolation("ensures clause failed", symbol="curriculum.trait_protocol.SimpleTask.complete", clause="ensures:4", phase="ensures", span={"end_byte":1432,"end_column":41,"end_line":64,"start_byte":1400,"start_column":9,"start_line":64}, expected="true", actual="false")
            if not ((len((self).title) > 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:0", phase="invariant", span={"end_byte":776,"end_column":33,"end_line":36,"start_byte":748,"start_column":5,"start_line":36}, expected="true", actual="false")
            if not (((self).urgency >= 0)):
                raise CottContractViolation("invariant failed", symbol="curriculum.trait_protocol.SimpleTask", clause="invariant:1", phase="invariant", span={"end_byte":808,"end_column":32,"end_line":37,"start_byte":781,"start_column":5,"start_line":37}, expected="true", actual="false")
            return _result

__all__ = ["Completable", "Prioritizable", "SimpleTask", "Summarizable", "format_summary", "inspect_task"]
