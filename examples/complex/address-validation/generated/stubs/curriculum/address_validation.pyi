from __future__ import annotations

from typing import TypeAlias, Union

from curriculum.address_validation_types import Address, AddressError, InvalidPostalCode
class Address: ...

AddressError: TypeAlias = Union[InvalidPostalCode]

def run() -> Result[Address, AddressError]: ...
