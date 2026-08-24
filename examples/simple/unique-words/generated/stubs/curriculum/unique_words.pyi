from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit
"""Normalize text with Unicode NFKC, full case folding, and NFKC again, then
return its words in source order. A word is a maximal sequence of Unicode
alphanumeric characters or underscores."""
def normalize_words(text: str) -> CottList[str]: ...

"""Return normalized words that occur exactly once, sorted in ascending
Unicode code-point order."""
def find_unique_words(text: str) -> CottList[str]: ...

__all__ = ["find_unique_words", "normalize_words"]
