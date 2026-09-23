package cott_impl.store.order

internal fun validate_line(line: store.order.OrderLine): cott_runtime.CottResult<store.order.OrderLine, store.order.OrderError> =
    if (line.quantity == 0u) {
        cott_runtime.Err(store.order.OrderError.InvalidQuantity(line.sku))
    } else {
        cott_runtime.Ok(line)
    }
