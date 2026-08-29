# order-management

## Purpose

Demonstrates a multi-module contract that separates the `store.catalog` and `store.order` modules, connecting catalog lookup results to order calculation.

## Key points

- `store.catalog` provides `Item`, `Catalog`, `CatalogError`, and `find_item`; it requires a non-empty SKU and returns the item for the requested SKU on success.
- `store.order` imports the catalog module's `Catalog` and `CatalogError`, and defines `OrderLine`, `Order`, `OrderReceipt`, `validate_line`, and `calculate_order`.
- `calculate_order` calls `validate_line` through the `store.order` public facade, then `store.catalog.find_item` through its public facade; it propagates the first validation error and wraps catalog `ItemNotFound` as `OrderError.ItemUnavailable`.
- It returns `OrderError.EmptyOrder` for an empty order, and a successful receipt preserves the original order's `order_id` while calculating quantities and the total in cents.
