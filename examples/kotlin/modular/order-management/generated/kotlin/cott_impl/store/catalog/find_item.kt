package cott_impl.store.catalog

internal fun find_item(catalog: store.catalog.Catalog, sku: kotlin.String): cott_runtime.CottResult<store.catalog.Item, store.catalog.CatalogError> {
    for (item in catalog.items) {
        if (item.sku == sku) {
            return cott_runtime.Ok(item)
        }
    }
    return cott_runtime.Err(store.catalog.CatalogError.ItemNotFound(sku))
}
