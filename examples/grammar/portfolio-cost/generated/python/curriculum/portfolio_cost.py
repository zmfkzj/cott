from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.portfolio_cost_types import Holding, PortfolioError, PortfolioError_NegativePrice, PortfolioError_NegativeShares, PortfolioError_NonFinitePrice, PortfolioError_TotalOverflow

def calculate_portfolio_cost(rows: CottList[Holding]) -> Result[F64, PortfolioError]:
    """Computes the total market value of a portfolio from a list of holdings.
Each holding supplies an I64 share count and an F64 price.

Holdings are processed in list order and evaluation stops at the first
error. For each holding, a negative share count returns NegativeShares;
otherwise a NaN or infinite price returns NonFinitePrice; otherwise a
price below zero returns NegativePrice. Zero shares, positive or negative
zero prices, and an empty list are accepted.

Starting from 0.0, each accepted share count is multiplied by its price
and the product is added to the running total using F64 arithmetic, in
list order. TotalOverflow is returned if either operation produces a
non-finite value. Otherwise Ok contains the finite, non-negative total;
ordinary F64 rounding and underflow are retained."""
    rows = _cott_validate_abi(rows, CottList[Holding], path="$.rows")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/portfolio_cost/calculate_portfolio_cost.py", "f10195afdca19baa480cc5fea1cfb0a4bbca07062ecef742bc236306118f11ac", "calculate_portfolio_cost", expected_project_name="portfolio-cost", expected_cott_symbol="curriculum.portfolio_cost.calculate_portfolio_cost")
        _result = _implementation(rows)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.portfolio_cost.calculate_portfolio_cost"
        if _error.span is None:
            _error.span = {"end_byte":1339,"end_column":1,"end_line":37,"start_byte":178,"start_column":1,"start_line":13}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.portfolio_cost.calculate_portfolio_cost", phase="implementation-call", span={"end_byte":1339,"end_column":1,"end_line":37,"start_byte":178,"start_column":1,"start_line":13}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.portfolio_cost.calculate_portfolio_cost", phase="implementation-call", span={"end_byte":1339,"end_column":1,"end_line":37,"start_byte":178,"start_column":1,"start_line":13}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[F64, PortfolioError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.portfolio_cost.calculate_portfolio_cost", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PortfolioError_NegativeShares, PortfolioError_NonFinitePrice, PortfolioError_NegativePrice, PortfolioError_TotalOverflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.portfolio_cost.calculate_portfolio_cost", phase="error", span={"end_byte":1339,"end_column":1,"end_line":37,"start_byte":178,"start_column":1,"start_line":13}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.portfolio_cost.calculate_portfolio_cost", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            total = _cott_match_value.value
            return ((total >= 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.portfolio_cost.calculate_portfolio_cost", clause="ensures:1", phase="ensures", span={"end_byte":1179,"end_column":45,"end_line":31,"start_byte":1139,"start_column":5,"start_line":31}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[F64, PortfolioError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["Holding", "PortfolioError", "PortfolioError_NegativePrice", "PortfolioError_NegativeShares", "PortfolioError_NonFinitePrice", "PortfolioError_TotalOverflow", "calculate_portfolio_cost"]
