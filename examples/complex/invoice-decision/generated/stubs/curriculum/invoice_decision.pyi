from __future__ import annotations

from typing import TypeAlias, Union

from curriculum.invoice_decision_types import InvoiceDecision, Approved, Rejected
InvoiceDecision: TypeAlias = Union[Approved, Rejected]

def run() -> InvoiceDecision: ...
