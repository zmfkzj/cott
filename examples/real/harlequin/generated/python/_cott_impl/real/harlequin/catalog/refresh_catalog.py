from cott_runtime import CottList, Ok, Result
from real.harlequin.catalog_types import CatalogError, CatalogRelation, CatalogScope, CatalogSnapshot
from real.harlequin.core_types import Connection


def refresh_catalog(connection: Connection, scope: CatalogScope) -> Result[CatalogSnapshot, CatalogError]:
    relations: CottList[CatalogRelation] = CottList(values=[])
    return Ok(value=CatalogSnapshot(scope=scope, relations=relations, refreshed_at=""))
