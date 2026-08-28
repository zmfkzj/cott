from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TextAnalysis:
    __hash__ = None
    total_lines: U64
    total_characters: U64
    total_words: U64
    unique_words: U64
    special_characters: U64

"""Case-fold `text` and return its Unicode alphanumeric words in source order.
Words are maximal nonempty runs of alphanumeric code points; all other
code points delimit words. No Unicode normalization is performed."""
"""Analyze `text` as Unicode code points.

Lines are separated only by U+000A. Characters exclude Unicode whitespace.
Words come from `extract_casefolded_words`; unique words use exact
code-point equality. Special characters are code points that are neither
alphanumeric nor whitespace."""
__all__ = ["TextAnalysis"]
