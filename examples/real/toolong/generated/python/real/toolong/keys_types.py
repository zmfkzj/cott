from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
"""A key press, named as Textual names keys: "up", "down", "left", "right",
"home", "end", "pageup", "pagedown", "insert", "delete", "backspace",
"enter", "escape", "tab", "shift+tab", "f1" ... "f12", "ctrl+a" ...
"ctrl+z", "ctrl+left", "ctrl+right", "ctrl+up", "ctrl+down", "ctrl+home",
"ctrl+end", "shift+left", "shift+right", "ctrl+backslash", "space",
"slash", and the character itself for every other printable character (so
"m" and "M" differ). character is the printable character typed, Nothing for
non-printable keys."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class KeyEvent:
    __hash__ = None
    key: str
    character: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "key", _cott_validate_abi(self.key, str, path="$.key"))
        if not _cott_validated_construction():
            object.__setattr__(self, "character", _cott_validate_abi(self.character, Option[str], path="$.character"))

"""Raw terminal input: one prompt_toolkit 3.0.52 key press, with name the
value of its Keys member (for example "c-f", "escape", "s-tab") or the
character itself for a character key, and data the text the terminal sent."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TerminalInput_KeyPress:
    __hash__ = None
    name: str
    data: str

TerminalInput: TypeAlias = Union[TerminalInput_KeyPress]

"""A Textual Input's editable state: its value and cursor position in code
points."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TextInput:
    __hash__ = None
    value: str
    cursor: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cursor", _cott_validate_abi(self.cursor, U64, path="$.cursor"))
        if not (_cott_contract_condition((((self).cursor <= len((self).value))), "real.toolong.keys.TextInput", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="real.toolong.keys.TextInput", clause="invariant:0", phase="invariant", span={"end_byte":1090,"end_column":44,"end_line":33,"start_byte":1051,"start_column":5,"start_line":33}, expected="true", actual="false")

"""The outcome of offering a key to a Textual Input: the input after the key,
whether the input consumed the key, whether its value changed, whether it
was submitted (enter) and whether the bell rings (a restricted character)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputEdit:
    __hash__ = None
    input: TextInput
    handled: bool
    changed: bool
    submitted: bool
    bell: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "input", _cott_validate_abi(self.input, TextInput, path="$.input"))
        if not _cott_validated_construction():
            object.__setattr__(self, "handled", _cott_validate_abi(self.handled, bool, path="$.handled"))
        if not _cott_validated_construction():
            object.__setattr__(self, "changed", _cott_validate_abi(self.changed, bool, path="$.changed"))
        if not _cott_validated_construction():
            object.__setattr__(self, "submitted", _cott_validate_abi(self.submitted, bool, path="$.submitted"))
        if not _cott_validated_construction():
            object.__setattr__(self, "bell", _cott_validate_abi(self.bell, bool, path="$.bell"))

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
__all__ = ["InputEdit", "KeyEvent", "TerminalInput", "TerminalInput_KeyPress", "TextInput"]
