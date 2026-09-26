from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.toolong.keys_types import InputEdit, KeyEvent, TerminalInput, TerminalInput_KeyPress, TextInput

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def decode_key(input: TerminalInput) -> Option[KeyEvent]:
    """Name a prompt_toolkit key press in Textual's key naming.

A name that is exactly one code point for which str.isprintable() is true
is a character key: " " gives key "space", "/" gives key "slash", any
other character gives key and character both that character; the
character of a character key is the name itself.

Otherwise, by name: "escape" escape; "c-i" tab; "c-m" and "c-j" enter;
"c-h" backspace; "s-tab" shift+tab; "up", "down", "left", "right",
"home", "end", "pageup", "pagedown", "insert", "delete" unchanged;
"c-left", "c-right", "c-up", "c-down", "c-home", "c-end" become
"ctrl+left" and so on; "s-left" and "s-right" become "shift+left" and
"shift+right"; "f1" to "f12" unchanged; "c-" followed by one backslash (Keys.ControlBackslash)
ctrl+backslash; any other
"c-" followed by one lowercase letter becomes "ctrl+" and that letter
("c-c" is "ctrl+c"). Every other name is Nothing. Keys that are not
character keys have no character; data is not used."""
    input = _cott_normalize_f32_abi(input, TerminalInput, path="$.input")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/keys/decode_key.py", "2bd6373821cb2b6d7eb5f2c4e5bff18295e40051a1370129038e6f76938b5dac", "decode_key", expected_project_name="toolong", expected_cott_symbol="real.toolong.keys.decode_key")
        _result = _implementation(input)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.keys.decode_key"
        if _error.span is None:
            _error.span = {"end_byte":2619,"end_column":1,"end_line":72,"start_byte":1439,"start_column":1,"start_line":47}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.keys.decode_key", phase="implementation-call", span={"end_byte":2619,"end_column":1,"end_line":72,"start_byte":1439,"start_column":1,"start_line":47}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.keys.decode_key", phase="implementation-call", span={"end_byte":2619,"end_column":1,"end_line":72,"start_byte":1439,"start_column":1,"start_line":47}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Option[KeyEvent], path="$.return")
    if _cott_test_context:
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Some and True:
                event = _cott_match_value.value
                return (_cott_contract_condition((((event).key != "")), "real.toolong.keys.decode_key", "ensures:1"))
            _cott_contract_condition((False), "real.toolong.keys.decode_key", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.keys.decode_key", clause="ensures:1", phase="ensures", span={"end_byte":2601,"end_column":50,"end_line":68,"start_byte":2556,"start_column":5,"start_line":68}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[KeyEvent], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def edit_input(input: TextInput, key: KeyEvent, suggestion: str, integer_only: bool) -> InputEdit:
    """Textual 0.52 Input key handling. The cursor is always kept within
[0, len(value)]. suggestion is the completion currently offered ("" for
none). The word-start pattern is re.compile(r"(?<=\\W)\\w").

A key with a printable character (str.isprintable()) inserts it at the
cursor and moves the cursor after it; when integer_only and the new value
does not fully match [-+]?\\d* the value is kept and the bell rings.
Otherwise by key:
left: cursor - 1. right: when the cursor is at the end and suggestion is
non-empty, the value becomes suggestion with the cursor at its end;
otherwise cursor + 1. ctrl+left: the start of the last word-start match in
value[:cursor], or 0. ctrl+right: cursor plus the start of the first
word-start match in value[cursor:], or the end. home and ctrl+a: 0. end and
ctrl+e: the end. backspace: delete the code point before the cursor (none
at 0) and move the cursor back. delete and ctrl+d: delete the code point at
the cursor. ctrl+w: when the cursor is not at 0, move it to the last
word-start match in value[:cursor] (0 when none) and delete what was
between. ctrl+u: delete everything before the cursor and move it to 0.
ctrl+f: with after = value[cursor:], delete up to the first word-start
match in after (keeping after from match end - 1), or everything after the
cursor when none matches. ctrl+k: delete everything after the cursor.
enter: submitted, nothing else changes.
handled is true for every key listed above and for printable characters;
any other key is not handled and leaves the input unchanged. changed is
true exactly when the value differs from input.value."""
    input = _cott_normalize_f32_abi(input, TextInput, path="$.input")
    key = _cott_normalize_f32_abi(key, KeyEvent, path="$.key")
    suggestion = _cott_normalize_f32_abi(suggestion, str, path="$.suggestion")
    integer_only = _cott_normalize_f32_abi(integer_only, bool, path="$.integer_only")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/keys/edit_input.py", "bbbdfe610e3a07e0aca377ab4d6fdb3b5ae4bb0143827b44e30e6cf0b2c51e0a", "edit_input", expected_project_name="toolong", expected_cott_symbol="real.toolong.keys.edit_input")
        _result = _implementation(input, key, suggestion, integer_only)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.keys.edit_input"
        if _error.span is None:
            _error.span = {"end_byte":4585,"end_column":1,"end_line":106,"start_byte":2619,"start_column":1,"start_line":72}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.keys.edit_input", phase="implementation-call", span={"end_byte":4585,"end_column":1,"end_line":106,"start_byte":2619,"start_column":1,"start_line":72}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.keys.edit_input", phase="implementation-call", span={"end_byte":4585,"end_column":1,"end_line":106,"start_byte":2619,"start_column":1,"start_line":72}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, InputEdit, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((not (not (_result).handled)) or ((_result).input == input))), "real.toolong.keys.edit_input", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.keys.edit_input", clause="ensures:1", phase="ensures", span={"end_byte":4499,"end_column":58,"end_line":101,"start_byte":4446,"start_column":5,"start_line":101}, expected="true", actual="false")
        if not (_cott_contract_condition((((_result).changed == (((_result).input).value != (input).value))), "real.toolong.keys.edit_input", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.keys.edit_input", clause="ensures:2", phase="ensures", span={"end_byte":4567,"end_column":68,"end_line":102,"start_byte":4504,"start_column":5,"start_line":102}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, InputEdit, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["InputEdit", "KeyEvent", "TerminalInput", "TerminalInput_KeyPress", "TextInput", "decode_key", "edit_input"]
