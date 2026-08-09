from __future__ import annotations

from typing import TypeAlias, Union

from curriculum.transfer_decision_types import AccountId, TransferDecision, Accepted, Rejected, TransferError, InsufficientFunds
class AccountId: ...

TransferDecision: TypeAlias = Union[Accepted, Rejected]

TransferError: TypeAlias = Union[InsufficientFunds]

def run() -> Result[TransferDecision, TransferError]: ...
