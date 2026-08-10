from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.textfile_analysis_types import TextAnalysis as TextAnalysis
"""Case-fold `text` and return its Unicode alphanumeric words in source order.
Words are maximal nonempty runs of alphanumeric code points; all other
code points delimit words. No Unicode normalization is performed."""
def extract_casefolded_words(text: str) -> CottList[str]: ...

"""Analyze `text` as Unicode code points.

Lines are separated only by U+000A. Characters exclude Unicode whitespace.
Words come from `extract_casefolded_words`; unique words use exact
code-point equality. Special characters are code points that are neither
alphanumeric nor whitespace."""
def analyze_text(text: str) -> TextAnalysis: ...

__all__ = ["TextAnalysis", "analyze_text", "extract_casefolded_words"]
