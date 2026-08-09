from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.address_validation_types import Address, AddressError, InvalidPostalCode

run = _cott_load("_cott_impl/curriculum/address_validation/run.py", "b29a55f8ed8f6e5d47dc7756d6cd30c28f81c0bc17625c14830dd10d99e2f233", "run")

__all__ = ["Address", "AddressError", "InvalidPostalCode", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
