from cott_runtime import CottList, Ok, Result
from real.harlequin.catalog_types import CatalogColumn
from real.harlequin.core_types import DatabaseTarget, SqlClientError


def catalog_columns(database: DatabaseTarget, relation: str) -> Result[CottList[CatalogColumn], SqlClientError]:
    columns: CottList[CatalogColumn] = CottList(values=[])
    return Ok(value=columns)
