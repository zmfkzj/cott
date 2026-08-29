from cott_runtime import Err, Ok, Result
from store.catalog_types import Catalog, CatalogError, CatalogError_ItemNotFound, Item


def find_item(catalog: Catalog, sku: str) -> Result[Item, CatalogError]:
    """Look up an item in the catalog by its SKU."""
    for item in catalog.items:
        if item.sku == sku:
            return Ok(value=item)
    return Err(error=CatalogError_ItemNotFound(sku=sku))
