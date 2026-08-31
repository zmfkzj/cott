from cott_runtime import CottList, Ok, Result
from real.harlequin.catalog_types import CatalogMatch
from real.harlequin.core_types import DatabaseTarget, SqlClientError


def search_catalog(database: DatabaseTarget, term: str) -> Result[CottList[CatalogMatch], SqlClientError]:
    catalog_matches: CottList[CatalogMatch] = CottList(values=[])
    return Ok(value=catalog_matches)
