from cott_runtime import CottList, Ok, Result
from real.harlequin.catalog_types import CatalogRelation
from real.harlequin.core_types import DatabaseTarget, SqlClientError


def catalog_relations(database: DatabaseTarget) -> Result[CottList[CatalogRelation], SqlClientError]:
    relations: CottList[CatalogRelation] = CottList(values=[])
    return Ok(value=relations)
