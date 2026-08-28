from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from store.order_types import Order as Order, OrderError as OrderError, OrderError_EmptyOrder as OrderError_EmptyOrder, OrderError_InvalidQuantity as OrderError_InvalidQuantity, OrderError_ItemUnavailable as OrderError_ItemUnavailable, OrderLine as OrderLine, OrderReceipt as OrderReceipt
from store.catalog_types import Catalog, CatalogError
"""Ensure an order line has positive quantity."""
def validate_line(line: OrderLine) -> Result[OrderLine, OrderError]: ...

"""Validate all order lines, lookup item prices, and produce a receipt."""
def calculate_order(catalog: Catalog, order: Order) -> Result[OrderReceipt, OrderError]: ...

__all__ = ["Order", "OrderError", "OrderError_EmptyOrder", "OrderError_InvalidQuantity", "OrderError_ItemUnavailable", "OrderLine", "OrderReceipt", "calculate_order", "validate_line"]
