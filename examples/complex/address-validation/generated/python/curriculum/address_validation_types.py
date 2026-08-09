from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class Address:
    line1: str
    city: str
    postal_code: str

@dataclass(frozen=True, slots=True, kw_only=True)
class InvalidPostalCode:
    pass

AddressError: TypeAlias = Union[InvalidPostalCode]

__all__ = ["Address", "AddressError", "InvalidPostalCode"]
