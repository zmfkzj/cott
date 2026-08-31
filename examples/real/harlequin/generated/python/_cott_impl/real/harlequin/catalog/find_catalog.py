from cott_runtime import CottList, Err, Ok, Result, U64
from real.harlequin.catalog_types import (
    CatalogError,
    CatalogError_LimitExceeded,
    CatalogMatch,
    CatalogMatchKind_Relation,
    CatalogSnapshot,
)


def find_catalog(snapshot: CatalogSnapshot, term: str, maximum_matches: U64) -> Result[CottList[CatalogMatch], CatalogError]:
    if maximum_matches > 1000:
        return Err(error=CatalogError_LimitExceeded(limit=1000))
    if maximum_matches == 0:
        return Ok(value=CottList(values=[]))

    normalized_term = term.casefold()
    found: list[CatalogMatch] = []
    for relation in snapshot.relations:
        if normalized_term not in relation.name.casefold():
            continue
        found.append(
            CatalogMatch(
                kind=CatalogMatchKind_Relation(),
                relation=relation.name,
                name=relation.name,
                ordinal=0,
            )
        )
        if len(found) >= maximum_matches:
            break

    return Ok(value=CottList(values=found))
