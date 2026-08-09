from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.transfer_decision_types import AccountId, TransferDecision, Accepted, Rejected, TransferError, InsufficientFunds

run = _cott_load("_cott_impl/curriculum/transfer_decision/run.py", "5778e72d17ad58e849423146b4e51e8380f10e44cd2eb35ce52a4d7edc6a0beb", "run")

__all__ = ["AccountId", "TransferDecision", "Accepted", "Rejected", "TransferError", "InsufficientFunds", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
