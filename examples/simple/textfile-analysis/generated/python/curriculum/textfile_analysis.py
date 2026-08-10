from __future__ import annotations

import dataclasses as _dataclasses
from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.textfile_analysis_types import TextAnalysis

def extract_casefolded_words(text: str) -> CottList[str]:
    """Case-fold `text` and return its Unicode alphanumeric words in source order.
Words are maximal nonempty runs of alphanumeric code points; all other
code points delimit words. No Unicode normalization is performed."""
    text = _cott_validate_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/textfile_analysis/extract_casefolded_words.py", "3b2b076ac907a28a0d3b751a99872520c7c65105bdac324dcf5ea47c51cc9a03", "extract_casefolded_words", expected_project_name="textfile-analysis", expected_cott_symbol="curriculum.textfile_analysis.extract_casefolded_words")
        _result = _implementation(text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.textfile_analysis.extract_casefolded_words"
        if _error.span is None:
            _error.span = {"end_byte":521,"end_column":1,"end_line":19,"start_byte":177,"start_column":1,"start_line":10}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.textfile_analysis.extract_casefolded_words", phase="implementation-call", span={"end_byte":521,"end_column":1,"end_line":19,"start_byte":177,"start_column":1,"start_line":10}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.textfile_analysis.extract_casefolded_words", phase="implementation-call", span={"end_byte":521,"end_column":1,"end_line":19,"start_byte":177,"start_column":1,"start_line":10}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    if not (((len(text) > 0) or (len(_result) == 0))):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.textfile_analysis.extract_casefolded_words", clause="ensures:1", phase="ensures", span={"end_byte":519,"end_column":44,"end_line":17,"start_byte":480,"start_column":5,"start_line":17}, expected="true", actual="false")
    return _result

def analyze_text(text: str) -> TextAnalysis:
    """Analyze `text` as Unicode code points.

Lines are separated only by U+000A. Characters exclude Unicode whitespace.
Words come from `extract_casefolded_words`; unique words use exact
code-point equality. Special characters are code points that are neither
alphanumeric nor whitespace."""
    text = _cott_validate_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/textfile_analysis/analyze_text.py", "801803519389d2683388ae3487a04391392ae709734f3b4a9ac85472ec6b76cb", "analyze_text", expected_project_name="textfile-analysis", expected_cott_symbol="curriculum.textfile_analysis.analyze_text")
        _result = _implementation(text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.textfile_analysis.analyze_text"
        if _error.span is None:
            _error.span = {"end_byte":1071,"end_column":1,"end_line":32,"start_byte":521,"start_column":1,"start_line":19}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.textfile_analysis.analyze_text", phase="implementation-call", span={"end_byte":1071,"end_column":1,"end_line":32,"start_byte":521,"start_column":1,"start_line":19}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.textfile_analysis.analyze_text", phase="implementation-call", span={"end_byte":1071,"end_column":1,"end_line":32,"start_byte":521,"start_column":1,"start_line":19}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, TextAnalysis, path="$.return")
    if not (((_result).unique_words <= (_result).total_words)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.textfile_analysis.analyze_text", clause="ensures:1", phase="ensures", span={"end_byte":947,"end_column":54,"end_line":29,"start_byte":898,"start_column":5,"start_line":29}, expected="true", actual="false")
    if not (((_result).total_words <= (_result).total_characters)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.textfile_analysis.analyze_text", clause="ensures:2", phase="ensures", span={"end_byte":1005,"end_column":58,"end_line":30,"start_byte":952,"start_column":5,"start_line":30}, expected="true", actual="false")
    if not (((_result).special_characters <= (_result).total_characters)):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.textfile_analysis.analyze_text", clause="ensures:3", phase="ensures", span={"end_byte":1070,"end_column":65,"end_line":31,"start_byte":1010,"start_column":5,"start_line":31}, expected="true", actual="false")
    return _result

__all__ = ["TextAnalysis", "analyze_text", "extract_casefolded_words"]
