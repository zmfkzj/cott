from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.billing_system_types import BillTotals as BillTotals, BillingError as BillingError, BillingError_DuplicateItem as BillingError_DuplicateItem, BillingError_NegativeQuantity as BillingError_NegativeQuantity, BillingError_WrongCategory as BillingError_WrongCategory, BillingItem as BillingItem, BillingItem_Coke as BillingItem_Coke, BillingItem_Daal as BillingItem_Daal, BillingItem_Dettol as BillingItem_Dettol, BillingItem_Fanta as BillingItem_Fanta, BillingItem_Flour as BillingItem_Flour, BillingItem_FoodOil as BillingItem_FoodOil, BillingItem_HandGloves as BillingItem_HandGloves, BillingItem_Limka as BillingItem_Limka, BillingItem_Maggi as BillingItem_Maggi, BillingItem_Mask as BillingItem_Mask, BillingItem_Mazza as BillingItem_Mazza, BillingItem_MountainDuo as BillingItem_MountainDuo, BillingItem_Newsprin as BillingItem_Newsprin, BillingItem_Rice as BillingItem_Rice, BillingItem_Sanitizer as BillingItem_Sanitizer, BillingItem_Sprite as BillingItem_Sprite, BillingItem_ThermalGun as BillingItem_ThermalGun, BillingItem_Wheat as BillingItem_Wheat, Quantity as Quantity
"""Validate all bill lines before any price or tax arithmetic. Validation makes three complete passes in priority order: any negative quantity returns NegativeQuantity; otherwise an item repeated anywhere across the three lists returns DuplicateItem; otherwise an item placed outside its medical, grocery, or drinks category returns WrongCategory. Zero quantities are valid and still participate in duplicate detection."""
def validate_bill_lines(medical: CottList[Quantity], grocery: CottList[Quantity], drinks: CottList[Quantity]) -> Result[Unit, BillingError]: ...

"""Validate the bill through validate_bill_lines, then calculate exact-cent subtotals and independently rounded taxes from this catalog of unit prices in cents: medical has Sanitizer 200, Mask 500, HandGloves 1200, Dettol 3000, Newsprin 500, and ThermalGun 1500; grocery has Rice 1000, FoodOil 1000, Wheat 1000, Daal 600, Flour 800, and Maggi 500; drinks has Sprite 1000, Limka 1000, Mazza 1000, Coke 1000, Fanta 1000, and MountainDuo 1000. Medical and grocery tax are 5 percent; drinks tax is 10 percent. Each tax is rounded to the nearest cent with ties to the even cent, and returned F64 fields are cent amounts divided by 100.

A validation error is returned unchanged. On success, the total is the sum of all three subtotals and all three rounded taxes."""
def calculate_bill(medical: CottList[Quantity], grocery: CottList[Quantity], drinks: CottList[Quantity]) -> Result[BillTotals, BillingError]: ...

__all__ = ["BillTotals", "BillingError", "BillingError_DuplicateItem", "BillingError_NegativeQuantity", "BillingError_WrongCategory", "BillingItem", "BillingItem_Coke", "BillingItem_Daal", "BillingItem_Dettol", "BillingItem_Fanta", "BillingItem_Flour", "BillingItem_FoodOil", "BillingItem_HandGloves", "BillingItem_Limka", "BillingItem_Maggi", "BillingItem_Mask", "BillingItem_Mazza", "BillingItem_MountainDuo", "BillingItem_Newsprin", "BillingItem_Rice", "BillingItem_Sanitizer", "BillingItem_Sprite", "BillingItem_ThermalGun", "BillingItem_Wheat", "Quantity", "calculate_bill", "validate_bill_lines"]
