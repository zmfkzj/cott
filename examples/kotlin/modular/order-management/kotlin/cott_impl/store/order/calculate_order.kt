package cott_impl.store.order

internal fun calculate_order(catalog: store.catalog.Catalog, order: store.order.Order): cott_runtime.CottResult<store.order.OrderReceipt, store.order.OrderError> {
    if (order.lines.isEmpty()) {
        return cott_runtime.Err(store.order.OrderError.EmptyOrder)
    }

    for (line in order.lines) {
        when (val validation = store.order.validate_line(line)) {
            is cott_runtime.Err -> return cott_runtime.Err(validation.error)
            is cott_runtime.Ok -> Unit
        }
    }

    var totalItems = 0u
    var totalCents = 0uL
    for (line in order.lines) {
        val item = when (val lookup = store.catalog.find_item(catalog, line.sku)) {
            is cott_runtime.Err -> return cott_runtime.Err(store.order.OrderError.ItemUnavailable(lookup.error))
            is cott_runtime.Ok -> lookup.value
        }
        if (line.quantity > UInt.MAX_VALUE - totalItems) {
            throw ArithmeticException("Order item count exceeds u32")
        }
        val quantity = line.quantity.toULong()
        if (quantity != 0uL && item.price_cents > (ULong.MAX_VALUE - totalCents) / quantity) {
            throw ArithmeticException("Order total exceeds u64")
        }
        totalItems += line.quantity
        totalCents += item.price_cents * quantity
    }

    return cott_runtime.Ok(store.order.OrderReceipt(order.order_id, totalItems, totalCents))
}
