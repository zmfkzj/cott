from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

def normalize_words(text: str) -> CottList[str]:
    """Normalize text with Unicode NFKC, full case folding, and NFKC again, then
return its words in source order. A word is a maximal sequence of Unicode
alphanumeric characters or underscores."""
    text = _cott_validate_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/unique_words/normalize_words.py", "63838f27569b43a6cd9c75b3c5cd68bd814316bb55a8f648286769f007ce049a", "normalize_words", expected_project_name="unique-words", expected_cott_symbol="curriculum.unique_words.normalize_words")
        _result = _implementation(text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.unique_words.normalize_words"
        if _error.span is None:
            _error.span = {"end_byte":342,"end_column":1,"end_line":12,"start_byte":32,"start_column":1,"start_line":3}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.unique_words.normalize_words", phase="implementation-call", span={"end_byte":342,"end_column":1,"end_line":12,"start_byte":32,"start_column":1,"start_line":3}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.unique_words.normalize_words", phase="implementation-call", span={"end_byte":342,"end_column":1,"end_line":12,"start_byte":32,"start_column":1,"start_line":3}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    if not (((len(text) > 0) or (len(_result) == 0))):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.unique_words.normalize_words", clause="ensures:1", phase="ensures", span={"end_byte":340,"end_column":44,"end_line":10,"start_byte":301,"start_column":5,"start_line":10}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=_cott_validate_abi)
    return _result

def find_unique_words(text: str) -> CottList[str]:
    """Return normalized words that occur exactly once, sorted in ascending
Unicode code-point order."""
    text = _cott_validate_abi(text, str, path="$.text")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/unique_words/find_unique_words.py", "f7e6b6bcbe5c5446dfc3b6c41da8cf7011010d7bc2a24c6ecbcded9cd537fa82", "find_unique_words", expected_project_name="unique-words", expected_cott_symbol="curriculum.unique_words.find_unique_words")
        _result = _implementation(text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.unique_words.find_unique_words"
        if _error.span is None:
            _error.span = {"end_byte":556,"end_column":1,"end_line":19,"start_byte":342,"start_column":1,"start_line":12}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.unique_words.find_unique_words", phase="implementation-call", span={"end_byte":556,"end_column":1,"end_line":19,"start_byte":342,"start_column":1,"start_line":12}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.unique_words.find_unique_words", phase="implementation-call", span={"end_byte":556,"end_column":1,"end_line":19,"start_byte":342,"start_column":1,"start_line":12}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[str], path="$.return")
    if not (((len(text) > 0) or (len(_result) == 0))):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.unique_words.find_unique_words", clause="ensures:1", phase="ensures", span={"end_byte":555,"end_column":44,"end_line":18,"start_byte":516,"start_column":5,"start_line":18}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["find_unique_words", "normalize_words"]
