from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Expense:
    __hash__ = None
    payer: str
    amount_cents: U64
    participants: CottList[str]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Transfer:
    __hash__ = None
    sender: str
    recipient: str
    cents: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Settlement:
    __hash__ = None
    transfers: CottList[Transfer]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Balance:
    __hash__ = None
    participant: str
    cents: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BalanceSheet:
    __hash__ = None
    debtors: CottList[Balance]
    creditors: CottList[Balance]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExpenseSplitError_BlankPayer:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExpenseSplitError_EmptyParticipants:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExpenseSplitError_DuplicateParticipant:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExpenseSplitError_PayerNotParticipant:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExpenseSplitError_ZeroAmount:
    pass

ExpenseSplitError: TypeAlias = Union[ExpenseSplitError_BlankPayer, ExpenseSplitError_EmptyParticipants, ExpenseSplitError_DuplicateParticipant, ExpenseSplitError_PayerNotParticipant, ExpenseSplitError_ZeroAmount]

"""Validate one expense and calculate exact integer-cent balances. Validation
priority is BlankPayer, EmptyParticipants, ZeroAmount,
DuplicateParticipant, then PayerNotParticipant. The expense is divided
evenly among alphabetically ordered participants, and remainder cents are
charged one at a time in that order. Returned debtor and creditor entries
are also ordered alphabetically. This pure function terminates for every
finite Expense."""
"""Greedily match alphabetically ordered debtors and creditors using exact
integer cents. Each transfer pays the smaller remaining balance, advancing
every exhausted side. Zero balances are consumed without stalling, so this
pure function terminates for every finite BalanceSheet."""
"""Calculate the expense's exact balances, propagate the first validation
error unchanged, and greedily settle every successful balance sheet."""
__all__ = ["Balance", "BalanceSheet", "Expense", "ExpenseSplitError", "ExpenseSplitError_BlankPayer", "ExpenseSplitError_DuplicateParticipant", "ExpenseSplitError_EmptyParticipants", "ExpenseSplitError_PayerNotParticipant", "ExpenseSplitError_ZeroAmount", "Settlement", "Transfer"]
