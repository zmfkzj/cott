from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.invoice_decision_types import InvoiceDecision, Approved, Rejected

run = _cott_load("_cott_impl/curriculum/invoice_decision/run.py", "a8d98f755f2ce6c87ffff43c4f6920dcecc8df8812ca77f6355fb20bad67d262", "run")

__all__ = ["InvoiceDecision", "Approved", "Rejected", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
