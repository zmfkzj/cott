from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.effects_selection_types import EffectError as EffectError, EffectError_InputMissing as EffectError_InputMissing, EffectError_OperationFailed as EffectError_OperationFailed
"""Read UTF-8 text from a compiler-owned filesystem fixture."""
def read_text(source: Path) -> Result[str, EffectError]: ...

"""Read source through its public facade and atomically replace destination."""
def copy_text(source: Path, destination: Path) -> Result[U64, EffectError]: ...

"""Fetch UTF-8 text from a compiler-owned local HTTP fixture."""
def fetch_local(url: str) -> Result[str, EffectError]: ...

"""Return whether a text effect result is successful."""
def text_result_is_ok(result: Result[str, EffectError]) -> bool: ...

"""Return successful text, or an empty string for an error result."""
def text_result_text(result: Result[str, EffectError]) -> str: ...

"""Return whether a copy effect result is successful."""
def copy_result_is_ok(result: Result[U64, EffectError]) -> bool: ...

"""Store value under key in a SQLite database, then read that value back."""
def store_and_load(database: Path, key: str, value: str) -> Result[str, EffectError]: ...

"""Return a compiler-owned deterministic fixture clock in nanoseconds."""
def clock_ns() -> U64: ...

"""Choose one index below limit from a deterministic seeded random stream."""
def sample_index(limit: U8, seed: U64) -> U8: ...

"""End the current process with code."""
def exit_with_code(code: U8) -> Never: ...

__all__ = ["EffectError", "EffectError_InputMissing", "EffectError_OperationFailed", "clock_ns", "copy_result_is_ok", "copy_text", "exit_with_code", "fetch_local", "read_text", "sample_index", "store_and_load", "text_result_is_ok", "text_result_text"]
