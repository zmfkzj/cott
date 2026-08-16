from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from store.catalog_types import Catalog as Catalog, CatalogError as CatalogError, CatalogError_ItemNotFound as CatalogError_ItemNotFound, Item as Item
"""Look up an item in the catalog by its SKU."""
def find_item(catalog: Catalog, sku: str) -> Result[Item, CatalogError]: ...

__all__ = ["Catalog", "CatalogError", "CatalogError_ItemNotFound", "Item", "find_item"]
