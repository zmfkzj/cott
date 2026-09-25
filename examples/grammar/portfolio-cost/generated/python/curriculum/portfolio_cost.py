from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from curriculum.portfolio_cost_types import Holding, MAX_F64, PortfolioError, PortfolioError_NegativePrice, PortfolioError_NegativeShares, PortfolioError_NonFinitePrice, PortfolioError_TotalOverflow

def calculate_portfolio_cost(rows: CottList[Holding]) -> Result[F64, PortfolioError]:
    """Computes the total market value of a portfolio: the sum of shares times
price over its holdings.

Holdings are examined one at a time in list order, and the first failing
holding decides the error. A holding fails with NegativeShares when its
share count is negative, otherwise with NonFinitePrice when its price is
NaN or infinite, otherwise with NegativePrice when its price is below zero.
Zero shares, signed-zero prices and an empty list are accepted.

The running total starts at 0.0. For each accepted holding, the share count
is converted to the nearest binary64 value and multiplied by the price, and
the product is added to the running total; every operation is binary64,
rounded to nearest, ties to even. If the product or the new running total
is not finite, TotalOverflow is returned at that holding, before later
holdings are examined."""
    rows = _cott_validate_abi(rows, CottList[Holding], path="$.rows")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/portfolio_cost/calculate_portfolio_cost.py", "86fa86d429f4511b36780cf05e4322df1eaf600574e288cbbc6e6f8ccbc04fb2", "calculate_portfolio_cost", expected_project_name="portfolio-cost", expected_cott_symbol="curriculum.portfolio_cost.calculate_portfolio_cost")
        _result = _implementation(rows)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.portfolio_cost.calculate_portfolio_cost"
        if _error.span is None:
            _error.span = {"end_byte":1450,"end_column":1,"end_line":41,"start_byte":223,"start_column":1,"start_line":15}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.portfolio_cost.calculate_portfolio_cost", phase="implementation-call", span={"end_byte":1450,"end_column":1,"end_line":41,"start_byte":223,"start_column":1,"start_line":15}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.portfolio_cost.calculate_portfolio_cost", phase="implementation-call", span={"end_byte":1450,"end_column":1,"end_line":41,"start_byte":223,"start_column":1,"start_line":15}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[F64, PortfolioError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.portfolio_cost.calculate_portfolio_cost", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (PortfolioError_NegativeShares, PortfolioError_NonFinitePrice, PortfolioError_NegativePrice, PortfolioError_TotalOverflow,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.portfolio_cost.calculate_portfolio_cost", phase="error", span={"end_byte":1450,"end_column":1,"end_line":41,"start_byte":223,"start_column":1,"start_line":15}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.portfolio_cost.calculate_portfolio_cost", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.portfolio_cost.calculate_portfolio_cost", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is PortfolioError_NegativeShares:
        _cott_contract_condition(True, "curriculum.portfolio_cost.calculate_portfolio_cost", "error:2")
    if type(_result) is Err and type(_result.error) is PortfolioError_NonFinitePrice:
        _cott_contract_condition(True, "curriculum.portfolio_cost.calculate_portfolio_cost", "error:3")
    if type(_result) is Err and type(_result.error) is PortfolioError_NegativePrice:
        _cott_contract_condition(True, "curriculum.portfolio_cost.calculate_portfolio_cost", "error:4")
    if type(_result) is Err and type(_result.error) is PortfolioError_TotalOverflow:
        _cott_contract_condition(True, "curriculum.portfolio_cost.calculate_portfolio_cost", "error:5")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            total = _cott_match_value.value
            return (_cott_contract_condition(((0 <= total <= MAX_F64)), "curriculum.portfolio_cost.calculate_portfolio_cost", "ensures:1"))
        _cott_contract_condition((False), "curriculum.portfolio_cost.calculate_portfolio_cost", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.portfolio_cost.calculate_portfolio_cost", clause="ensures:1", phase="ensures", span={"end_byte":1289,"end_column":56,"end_line":34,"start_byte":1238,"start_column":5,"start_line":34}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[F64, PortfolioError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["Holding", "MAX_F64", "PortfolioError", "PortfolioError_NegativePrice", "PortfolioError_NegativeShares", "PortfolioError_NonFinitePrice", "PortfolioError_TotalOverflow", "calculate_portfolio_cost"]
