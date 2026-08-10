from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.expense_split_types import Balance as Balance, BalanceSheet as BalanceSheet, Expense as Expense, ExpenseSplitError as ExpenseSplitError, ExpenseSplitError_BlankPayer as ExpenseSplitError_BlankPayer, ExpenseSplitError_DuplicateParticipant as ExpenseSplitError_DuplicateParticipant, ExpenseSplitError_EmptyParticipants as ExpenseSplitError_EmptyParticipants, ExpenseSplitError_PayerNotParticipant as ExpenseSplitError_PayerNotParticipant, ExpenseSplitError_ZeroAmount as ExpenseSplitError_ZeroAmount, Settlement as Settlement, Transfer as Transfer
"""Validate one expense and calculate exact integer-cent balances. Validation
priority is BlankPayer, EmptyParticipants, ZeroAmount,
DuplicateParticipant, then PayerNotParticipant. The expense is divided
evenly among alphabetically ordered participants, and remainder cents are
charged one at a time in that order. Returned debtor and creditor entries
are also ordered alphabetically. This pure function terminates for every
finite Expense."""
def calculate_balances(expense: Expense) -> Result[BalanceSheet, ExpenseSplitError]: ...

"""Greedily match alphabetically ordered debtors and creditors using exact
integer cents. Each transfer pays the smaller remaining balance, advancing
every exhausted side. Zero balances are consumed without stalling, so this
pure function terminates for every finite BalanceSheet."""
def settle_balances(balances: BalanceSheet) -> Settlement: ...

"""Calculate the expense's exact balances, propagate the first validation
error unchanged, and greedily settle every successful balance sheet."""
def settle_expense(expense: Expense) -> Result[Settlement, ExpenseSplitError]: ...

__all__ = ["Balance", "BalanceSheet", "Expense", "ExpenseSplitError", "ExpenseSplitError_BlankPayer", "ExpenseSplitError_DuplicateParticipant", "ExpenseSplitError_EmptyParticipants", "ExpenseSplitError_PayerNotParticipant", "ExpenseSplitError_ZeroAmount", "Settlement", "Transfer", "calculate_balances", "settle_balances", "settle_expense"]
