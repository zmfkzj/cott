import cott_runtime.CottList
import cott_runtime.Err
import cott_runtime.Ok
import store.catalog.Catalog
import store.catalog.Item
import store.catalog.find_item
import store.order.Order
import store.order.OrderLine
import store.order.calculate_order

private fun formatCents(value: ULong): String =
    "${value / 100uL}.${(value % 100uL).toString().padStart(2, '0')}"

fun main() {
    val catalog = Catalog(
        items = CottList(
            listOf(
                Item(sku = "SKU-APPLE", name = "Honeycrisp Apple", price_cents = 150uL),
                Item(sku = "SKU-BANANA", name = "Organic Banana", price_cents = 75uL),
                Item(sku = "SKU-COFFEE", name = "Dark Roast Coffee", price_cents = 1200uL),
            ),
        ),
    )

    when (val itemResult = find_item(catalog, "SKU-APPLE")) {
        is Ok -> println("Catalog lookup: ${itemResult.value.name} (\$${formatCents(itemResult.value.price_cents)})")
        is Err -> println("Catalog lookup failed: ${itemResult.error}")
    }

    val order = Order(
        order_id = "ORD-2026-001",
        lines = CottList(
            listOf(
                OrderLine(sku = "SKU-APPLE", quantity = 4u),
                OrderLine(sku = "SKU-COFFEE", quantity = 2u),
            ),
        ),
    )

    when (val receiptResult = calculate_order(catalog, order)) {
        is Ok -> {
            val receipt = receiptResult.value
            println(
                "Order ${receipt.order_id}: ${receipt.total_items} items, " +
                    "total \$${formatCents(receipt.total_cents)}",
            )
        }
        is Err -> println("Order calculation failed: ${receiptResult.error}")
    }
}
