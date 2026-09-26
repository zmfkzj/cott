from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.toolong.keys_types import InputEdit as InputEdit, KeyEvent as KeyEvent, TerminalInput as TerminalInput, TerminalInput_KeyPress as TerminalInput_KeyPress, TextInput as TextInput
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
def decode_key(input: TerminalInput) -> Option[KeyEvent]: ...

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
def edit_input(input: TextInput, key: KeyEvent, suggestion: str, integer_only: bool) -> InputEdit: ...

__all__ = ["InputEdit", "KeyEvent", "TerminalInput", "TerminalInput_KeyPress", "TextInput", "decode_key", "edit_input"]
