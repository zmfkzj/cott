from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottExternal, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Sanitizer:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Mask:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_HandGloves:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Dettol:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Newsprin:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_ThermalGun:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Rice:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_FoodOil:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Wheat:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Daal:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Flour:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Maggi:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Sprite:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Limka:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Mazza:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Coke:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_Fanta:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingItem_MountainDuo:
    pass

BillingItem: TypeAlias = Union[BillingItem_Sanitizer, BillingItem_Mask, BillingItem_HandGloves, BillingItem_Dettol, BillingItem_Newsprin, BillingItem_ThermalGun, BillingItem_Rice, BillingItem_FoodOil, BillingItem_Wheat, BillingItem_Daal, BillingItem_Flour, BillingItem_Maggi, BillingItem_Sprite, BillingItem_Limka, BillingItem_Mazza, BillingItem_Coke, BillingItem_Fanta, BillingItem_MountainDuo]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingError_NegativeQuantity:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingError_DuplicateItem:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillingError_WrongCategory:
    pass

BillingError: TypeAlias = Union[BillingError_NegativeQuantity, BillingError_DuplicateItem, BillingError_WrongCategory]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Quantity:
    __hash__ = None
    item: BillingItem
    quantity: I64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BillTotals:
    __hash__ = None
    medical_subtotal: F64
    grocery_subtotal: F64
    drinks_subtotal: F64
    medical_tax: F64
    grocery_tax: F64
    drinks_tax: F64
    total: F64

"""Validate all bill lines before any price or tax arithmetic. Validation makes three complete passes in priority order: any negative quantity returns NegativeQuantity; otherwise an item repeated anywhere across the three lists returns DuplicateItem; otherwise an item placed outside its medical, grocery, or drinks category returns WrongCategory. Zero quantities are valid and still participate in duplicate detection."""
"""Validate the bill through validate_bill_lines, then calculate exact-cent subtotals and independently rounded taxes from this catalog of unit prices in cents: medical has Sanitizer 200, Mask 500, HandGloves 1200, Dettol 3000, Newsprin 500, and ThermalGun 1500; grocery has Rice 1000, FoodOil 1000, Wheat 1000, Daal 600, Flour 800, and Maggi 500; drinks has Sprite 1000, Limka 1000, Mazza 1000, Coke 1000, Fanta 1000, and MountainDuo 1000. Medical and grocery tax are 5 percent; drinks tax is 10 percent. Each tax is rounded to the nearest cent with ties to the even cent, and returned F64 fields are cent amounts divided by 100.

A validation error is returned unchanged. On success, the total is the sum of all three subtotals and all three rounded taxes."""
__all__ = ["BillTotals", "BillingError", "BillingError_DuplicateItem", "BillingError_NegativeQuantity", "BillingError_WrongCategory", "BillingItem", "BillingItem_Coke", "BillingItem_Daal", "BillingItem_Dettol", "BillingItem_Fanta", "BillingItem_Flour", "BillingItem_FoodOil", "BillingItem_HandGloves", "BillingItem_Limka", "BillingItem_Maggi", "BillingItem_Mask", "BillingItem_Mazza", "BillingItem_MountainDuo", "BillingItem_Newsprin", "BillingItem_Rice", "BillingItem_Sanitizer", "BillingItem_Sprite", "BillingItem_ThermalGun", "BillingItem_Wheat", "Quantity"]
