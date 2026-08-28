from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.expense_split_types import Balance, BalanceSheet, Expense, ExpenseSplitError, ExpenseSplitError_BlankPayer, ExpenseSplitError_DuplicateParticipant, ExpenseSplitError_EmptyParticipants, ExpenseSplitError_PayerNotParticipant, ExpenseSplitError_ZeroAmount, Settlement, Transfer

def calculate_balances(expense: Expense) -> Result[BalanceSheet, ExpenseSplitError]:
    """Validate one expense and calculate exact integer-cent balances. Validation
priority is BlankPayer, EmptyParticipants, ZeroAmount,
DuplicateParticipant, then PayerNotParticipant. The expense is divided
evenly among alphabetically ordered participants, and remainder cents are
charged one at a time in that order. Returned debtor and creditor entries
are also ordered alphabetically. This pure function terminates for every
finite Expense."""
    expense = _cott_validate_abi(expense, Expense, path="$.expense")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((expense).payer) == 0)):
        _expected_error = ExpenseSplitError_BlankPayer
        _expected_error_span = {"end_byte":1239,"end_column":67,"end_line":44,"start_byte":1177,"start_column":5,"start_line":44}
        _expected_error_clause = "error:2"
    if _expected_error is None and ((len((expense).participants) == 0)):
        _expected_error = ExpenseSplitError_EmptyParticipants
        _expected_error_span = {"end_byte":1320,"end_column":81,"end_line":45,"start_byte":1244,"start_column":5,"start_line":45}
        _expected_error_clause = "error:3"
    if _expected_error is None and (((expense).amount_cents == 0)):
        _expected_error = ExpenseSplitError_ZeroAmount
        _expected_error_span = {"end_byte":1390,"end_column":70,"end_line":46,"start_byte":1325,"start_column":5,"start_line":46}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/expense_split/calculate_balances.py", "bd176de8bd1fc8917b9fc516400321a3788e821f73afc5c1d2a0b0e3a625c5ec", "calculate_balances", expected_project_name="expense-split", expected_cott_symbol="curriculum.expense_split.calculate_balances")
        _result = _implementation(expense)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.expense_split.calculate_balances"
        if _error.span is None:
            _error.span = {"end_byte":1505,"end_column":1,"end_line":52,"start_byte":490,"start_column":1,"start_line":31}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.expense_split.calculate_balances", phase="implementation-call", span={"end_byte":1505,"end_column":1,"end_line":52,"start_byte":490,"start_column":1,"start_line":31}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.expense_split.calculate_balances", phase="implementation-call", span={"end_byte":1505,"end_column":1,"end_line":52,"start_byte":490,"start_column":1,"start_line":31}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[BalanceSheet, ExpenseSplitError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.expense_split.calculate_balances", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ExpenseSplitError_DuplicateParticipant, ExpenseSplitError_PayerNotParticipant,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.expense_split.calculate_balances", phase="error", span={"end_byte":1505,"end_column":1,"end_line":52,"start_byte":490,"start_column":1,"start_line":31}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.expense_split.calculate_balances", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            balances = _cott_match_value.value
            return (((len((balances).debtors) + len((balances).creditors)) <= len((expense).participants)))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.expense_split.calculate_balances", clause="ensures:1", phase="ensures", span={"end_byte":1171,"end_column":111,"end_line":42,"start_byte":1065,"start_column":5,"start_line":42}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[BalanceSheet, ExpenseSplitError], path="$.return", validator=_cott_validate_abi)
    return _result

def settle_balances(balances: BalanceSheet) -> Settlement:
    """Greedily match alphabetically ordered debtors and creditors using exact
integer cents. Each transfer pays the smaller remaining balance, advancing
every exhausted side. Zero balances are consumed without stalling, so this
pure function terminates for every finite BalanceSheet."""
    balances = _cott_validate_abi(balances, BalanceSheet, path="$.balances")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/expense_split/settle_balances.py", "8b303f0070e6943b646556e30d276679dfc8fafb1ab1650b28571b6ce612ccf4", "settle_balances", expected_project_name="expense-split", expected_cott_symbol="curriculum.expense_split.settle_balances")
        _result = _implementation(balances)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.expense_split.settle_balances"
        if _error.span is None:
            _error.span = {"end_byte":1979,"end_column":1,"end_line":64,"start_byte":1505,"start_column":1,"start_line":52}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.expense_split.settle_balances", phase="implementation-call", span={"end_byte":1979,"end_column":1,"end_line":64,"start_byte":1505,"start_column":1,"start_line":52}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.expense_split.settle_balances", phase="implementation-call", span={"end_byte":1979,"end_column":1,"end_line":64,"start_byte":1505,"start_column":1,"start_line":52}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Settlement, path="$.return")
    if not ((len((_result).transfers) <= (len((balances).debtors) + len((balances).creditors)))):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.expense_split.settle_balances", clause="ensures:1", phase="ensures", span={"end_byte":1961,"end_column":84,"end_line":60,"start_byte":1882,"start_column":5,"start_line":60}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Settlement, path="$.return", validator=_cott_validate_abi)
    return _result

def settle_expense(expense: Expense) -> Result[Settlement, ExpenseSplitError]:
    """Calculate the expense's exact balances, propagate the first validation
error unchanged, and greedily settle every successful balance sheet."""
    expense = _cott_validate_abi(expense, Expense, path="$.expense")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((expense).payer) == 0)):
        _expected_error = ExpenseSplitError_BlankPayer
        _expected_error_span = {"end_byte":2383,"end_column":67,"end_line":72,"start_byte":2321,"start_column":5,"start_line":72}
        _expected_error_clause = "error:2"
    if _expected_error is None and ((len((expense).participants) == 0)):
        _expected_error = ExpenseSplitError_EmptyParticipants
        _expected_error_span = {"end_byte":2464,"end_column":81,"end_line":73,"start_byte":2388,"start_column":5,"start_line":73}
        _expected_error_clause = "error:3"
    if _expected_error is None and (((expense).amount_cents == 0)):
        _expected_error = ExpenseSplitError_ZeroAmount
        _expected_error_span = {"end_byte":2534,"end_column":70,"end_line":74,"start_byte":2469,"start_column":5,"start_line":74}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/expense_split/settle_expense.py", "bbf71f60a8d95855e80d399efe6a5a36d842082f0154eb0b340bf705ade9bce2", "settle_expense", expected_project_name="expense-split", expected_cott_symbol="curriculum.expense_split.settle_expense")
        _result = _implementation(expense)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.expense_split.settle_expense"
        if _error.span is None:
            _error.span = {"end_byte":2648,"end_column":1,"end_line":79,"start_byte":1979,"start_column":1,"start_line":64}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.expense_split.settle_expense", phase="implementation-call", span={"end_byte":2648,"end_column":1,"end_line":79,"start_byte":1979,"start_column":1,"start_line":64}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.expense_split.settle_expense", phase="implementation-call", span={"end_byte":2648,"end_column":1,"end_line":79,"start_byte":1979,"start_column":1,"start_line":64}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Settlement, ExpenseSplitError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.expense_split.settle_expense", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ExpenseSplitError_DuplicateParticipant, ExpenseSplitError_PayerNotParticipant,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.expense_split.settle_expense", phase="error", span={"end_byte":2648,"end_column":1,"end_line":79,"start_byte":1979,"start_column":1,"start_line":64}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.expense_split.settle_expense", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            settlement = _cott_match_value.value
            return ((len((settlement).transfers) <= len((expense).participants)))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.expense_split.settle_expense", clause="ensures:1", phase="ensures", span={"end_byte":2315,"end_column":90,"end_line":70,"start_byte":2230,"start_column":5,"start_line":70}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Settlement, ExpenseSplitError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["Balance", "BalanceSheet", "Expense", "ExpenseSplitError", "ExpenseSplitError_BlankPayer", "ExpenseSplitError_DuplicateParticipant", "ExpenseSplitError_EmptyParticipants", "ExpenseSplitError_PayerNotParticipant", "ExpenseSplitError_ZeroAmount", "Settlement", "Transfer", "calculate_balances", "settle_balances", "settle_expense"]
