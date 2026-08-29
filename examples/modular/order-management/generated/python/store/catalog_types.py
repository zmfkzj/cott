from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Item:
    __hash__ = None
    sku: str
    name: str
    price_cents: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "sku", _cott_validate_abi(self.sku, str, path="$.sku"))
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "price_cents", _cott_validate_abi(self.price_cents, U64, path="$.price_cents"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Catalog:
    __hash__ = None
    items: CottList[Item]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "items", _cott_validate_abi(self.items, CottList[Item], path="$.items"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogError_ItemNotFound:
    __hash__ = None
    sku: str

CatalogError: TypeAlias = Union[CatalogError_ItemNotFound]

"""Look up an item in the catalog by its SKU."""
__all__ = ["Catalog", "CatalogError", "CatalogError_ItemNotFound", "Item"]
