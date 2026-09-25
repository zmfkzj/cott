from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from store.catalog_types import Catalog as Catalog, CatalogError as CatalogError, CatalogError_ItemNotFound as CatalogError_ItemNotFound, Item as Item
"""Look up the catalog item whose SKU is `sku`. SKUs are unique within a catalog, so at most
one item matches."""
def find_item(catalog: Catalog, sku: str) -> Result[Item, CatalogError]: ...

__all__ = ["Catalog", "CatalogError", "CatalogError_ItemNotFound", "Item", "find_item"]
