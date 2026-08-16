from cott_runtime import CottList, Err, Ok, U32, U64
from store.catalog import find_item
from store.catalog_types import Catalog, Item
from store.order import calculate_order
from store.order_types import Order, OrderLine


def main() -> None:
    # 1. Build a catalog with inventory items
    catalog = Catalog(
        items=CottList(
            values=[
                Item(sku="SKU-APPLE", name="Honeycrisp Apple", price_cents=U64(150)),
                Item(sku="SKU-BANANA", name="Organic Banana", price_cents=U64(75)),
                Item(sku="SKU-COFFEE", name="Dark Roast Coffee", price_cents=U64(1200)),
            ]
        )
    )

    # 2. Query the catalog module directly
    item_res = find_item(catalog, "SKU-APPLE")
    if isinstance(item_res, Ok):
        print(f"Catalog lookup: {item_res.value.name} (${item_res.value.price_cents / 100:.2f})")
    else:
        print(f"Catalog lookup failed: {item_res.error}")

    # 3. Create and process a multi-item order across both modules
    order = Order(
        order_id="ORD-2026-001",
        lines=CottList(
            values=[
                OrderLine(sku="SKU-APPLE", quantity=U32(4)),
                OrderLine(sku="SKU-COFFEE", quantity=U32(2)),
            ]
        ),
    )

    receipt_res = calculate_order(catalog, order)
    if isinstance(receipt_res, Ok):
        receipt = receipt_res.value
        print(
            f"Order {receipt.order_id}: {receipt.total_items} items, "
            f"total ${receipt.total_cents / 100:.2f}"
        )
    else:
        print(f"Order calculation failed: {receipt_res.error}")


if __name__ == "__main__":
    main()
