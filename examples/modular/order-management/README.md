# order-management

## Purpose

Demonstrates a multi-module contract that separates the `store.catalog` and `store.order` modules, connecting catalog lookup results to order calculation.

## Key points

- `store.catalog` provides `Item`, `Catalog`, `CatalogError`, and `find_item`; it requires a non-empty SKU and returns the item for the requested SKU on success.
- `store.order` imports the catalog module's `Catalog`, `CatalogError`, and `Item`, and defines `OrderLine`, `Order`, `OrderReceipt`, `validate_line`, and `calculate_order`.
- `calculate_order` validates each `OrderLine` with `validate_line`, then looks up its price with `find_item`; it wraps the catalog's `ItemNotFound` as `OrderError.ItemUnavailable` to represent an error crossing the module boundary.
- It returns `OrderError.EmptyOrder` for an empty order, and a successful receipt preserves the original order's `order_id` while calculating quantities and the total in cents.
