from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

A = TypeVar("A")
B = TypeVar("B")

def make_coordinate_pair(x: I32, y: I32) -> tuple[I32, I32]:
    """Create a pair tuple representing 2D integer coordinates."""
    x = _cott_validate_abi(x, I32, path="$.x")
    y = _cott_validate_abi(y, I32, path="$.y")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/pair_tuple/make_coordinate_pair.py", "e30c945d8ac522eabbda25c6c4d09ee1d073e2959bd47b36af03b0e01d9cefd3", "make_coordinate_pair", expected_project_name="pair-tuple", expected_cott_symbol="curriculum.pair_tuple.make_coordinate_pair")
        _result = _implementation(x, y)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.pair_tuple.make_coordinate_pair"
        if _error.span is None:
            _error.span = {"end_byte":188,"end_column":1,"end_line":10,"start_byte":30,"start_column":1,"start_line":3}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.pair_tuple.make_coordinate_pair", phase="implementation-call", span={"end_byte":188,"end_column":1,"end_line":10,"start_byte":30,"start_column":1,"start_line":3}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.pair_tuple.make_coordinate_pair", phase="implementation-call", span={"end_byte":188,"end_column":1,"end_line":10,"start_byte":30,"start_column":1,"start_line":3}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, tuple[I32, I32], path="$.return")
    return _result

def swap_pair(pair: tuple[A, B]) -> tuple[B, A]:
    """Swap the elements of a generic pair tuple."""
    pair = _cott_validate_abi(pair, tuple[A, B], path="$.pair")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/pair_tuple/swap_pair.py", "8dfb3a1d5e8ad4ba3eb14d35cbaafeed780111d6ea369b89b7b7ca79f21b414f", "swap_pair", expected_project_name="pair-tuple", expected_cott_symbol="curriculum.pair_tuple.swap_pair")
        _result = _implementation(pair)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.pair_tuple.swap_pair"
        if _error.span is None:
            _error.span = {"end_byte":325,"end_column":1,"end_line":16,"start_byte":188,"start_column":1,"start_line":10}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.pair_tuple.swap_pair", phase="implementation-call", span={"end_byte":325,"end_column":1,"end_line":16,"start_byte":188,"start_column":1,"start_line":10}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.pair_tuple.swap_pair", phase="implementation-call", span={"end_byte":325,"end_column":1,"end_line":16,"start_byte":188,"start_column":1,"start_line":10}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, tuple[B, A], path="$.return")
    return _result

__all__ = ["make_coordinate_pair", "swap_pair"]
