package cott_impl.store.order

internal fun calculate_order(catalog: store.catalog.Catalog, order: store.order.Order): cott_runtime.CottResult<store.order.OrderReceipt, store.order.OrderError> {
    if (order.lines.isEmpty()) {
        return cott_runtime.Err(store.order.OrderError.EmptyOrder)
    }

    var totalItems = 0u
    var totalCents = 0uL
    for (line in order.lines) {
        val valid = when (val validation = store.order.validate_line(line)) {
            is cott_runtime.Err -> return cott_runtime.Err(validation.error)
            is cott_runtime.Ok -> validation.value
        }
        val item = when (val lookup = store.catalog.find_item(catalog, valid.sku)) {
            is cott_runtime.Err -> return cott_runtime.Err(store.order.OrderError.ItemUnavailable(lookup.error))
            is cott_runtime.Ok -> lookup.value
        }
        totalItems += valid.quantity
        totalCents += item.price_cents * valid.quantity.toULong()
    }

    return cott_runtime.Ok(store.order.OrderReceipt(order.order_id, totalItems, totalCents))
}
