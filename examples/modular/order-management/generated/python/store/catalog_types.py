from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Item:
    __hash__ = None
    sku: str
    name: str
    price_cents: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Catalog:
    __hash__ = None
    items: CottList[Item]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogError_ItemNotFound:
    __hash__ = None
    sku: str

CatalogError: TypeAlias = Union[CatalogError_ItemNotFound]

"""Look up an item in the catalog by its SKU."""
__all__ = ["Catalog", "CatalogError", "CatalogError_ItemNotFound", "Item"]
