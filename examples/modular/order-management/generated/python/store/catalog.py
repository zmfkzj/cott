from __future__ import annotations

import dataclasses as _dataclasses
from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from store.catalog_types import Catalog, CatalogError, CatalogError_ItemNotFound, Item

def find_item(catalog: Catalog, sku: str) -> Result[Item, CatalogError]:
    """Look up an item in the catalog by its SKU."""
    catalog = _cott_validate_abi(catalog, Catalog, path="$.catalog")
    sku = _cott_validate_abi(sku, str, path="$.sku")
    if not ((len(sku) > 0)):
        raise CottContractViolation("requires clause failed", symbol="store.catalog.find_item", clause="requires:1", phase="requires", span={"end_byte":334,"end_column":25,"end_line":19,"start_byte":314,"start_column":5,"start_line":19}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/store/catalog/find_item.py", "e54a5ad6b22fd5efb8c01891012f2baf03b47bcfe2f80099cba5062a1f8297bb", "find_item", expected_project_name="order-management", expected_cott_symbol="store.catalog.find_item")
        _result = _implementation(catalog, sku)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "store.catalog.find_item"
        if _error.span is None:
            _error.span = {"end_byte":420,"end_column":1,"end_line":24,"start_byte":170,"start_column":1,"start_line":14}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="store.catalog.find_item", phase="implementation-call", span={"end_byte":420,"end_column":1,"end_line":24,"start_byte":170,"start_column":1,"start_line":14}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="store.catalog.find_item", phase="implementation-call", span={"end_byte":420,"end_column":1,"end_line":24,"start_byte":170,"start_column":1,"start_line":14}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Item, CatalogError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="store.catalog.find_item", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CatalogError_ItemNotFound,):
            raise CottContractViolation("returned error is not allowed", symbol="store.catalog.find_item", phase="error", span={"end_byte":420,"end_column":1,"end_line":24,"start_byte":170,"start_column":1,"start_line":14}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="store.catalog.find_item", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        item = _result.value
        if not (((item).sku == sku)):
            raise CottContractViolation("ensures clause failed", symbol="store.catalog.find_item", clause="ensures:2", phase="ensures", span={"end_byte":382,"end_column":47,"end_line":21,"start_byte":340,"start_column":5,"start_line":21}, expected="true", actual="false")
    return _result

__all__ = ["Catalog", "CatalogError", "CatalogError_ItemNotFound", "Item", "find_item"]
