# order-management

## Purpose

Demonstrates a multi-module contract: `store.catalog` owns catalog types and lookup, and `store.order` composes that lookup with line validation through public facades.

## Key points

- `store.catalog` owns `Item`, `Catalog`, `CatalogError` and `find_item`. A `Catalog` invariant (`unique_by(self.items, Item.sku)`) makes SKUs unique, so a lookup has one answer. `find_item` requires a non-empty SKU, returns an item with that SKU, and names the requested SKU in `ItemNotFound`.
- `store.order` owns `OrderLine` (invariant: non-empty SKU), `Order`, `OrderReceipt`, `OrderError`, `validate_line` and `calculate_order`, and imports `Catalog` and `CatalogError` from the catalog module.
- `validate_line` uses `errors complete`: it returns the line unchanged unless its quantity is zero, and then reports `InvalidQuantity` with the line's SKU.
- `calculate_order` is the composition root. Its formal clauses cover `EmptyOrder` for an empty order and the receipt's `order_id`. Requirements state the rest: validation and pricing go through the `validate_line` and `find_item` facades; lines are processed in order, validating each line before its lookup; the first failure wins, a validation error propagates unchanged and a catalog error becomes `ItemUnavailable(cause)`; the totals count every line at its catalog price. The `doc` defines the totals in cents and leaves totals beyond `U32` items or `U64` cents outside the contract.

## Evidence

- `store.catalog` scenario `lookup_by_sku` checks a found item's name and price and a missing SKU; it backs `RETURNS_CATALOG_ITEM`.
- End-to-end scenarios live in `store.order` and run the real catalog lookup: `receipt_counts_every_line` checks the totals of an order that repeats a SKU (`RECEIPT_COUNTS_EVERY_LINE`), and `first_failing_line_decides` checks the error priority and the wrapped cause (`FIRST_FAILING_LINE_DECIDES`).
- `COMPOSES_THROUGH_FACADES` stays `unverified`: no scenario can tell a facade call from duplicated logic that returns the same result.
- `python/app.py` prints a catalog lookup and a two-line order receipt; the repository test `tests/examples.rs` checks that output. It is a program regression, not Cott evidence.
