from typing import Final

from cott_runtime import CottList, Err, Ok, Result, U64
from real.harlequin.catalog_types import CatalogError, CatalogError_LimitExceeded, CatalogMatch, CatalogMatchKind_Relation, CatalogSnapshot

_MAX_MATCHES: Final[int] = 1000


def find_catalog(snapshot: CatalogSnapshot, term: str, maximum_matches: U64) -> Result[CottList[CatalogMatch], CatalogError]:
    if maximum_matches > _MAX_MATCHES:
        return Err(error=CatalogError_LimitExceeded(limit=_MAX_MATCHES))
    found: list[CatalogMatch] = []
    if maximum_matches > 0:
        needle = term.casefold()
        for relation in snapshot.relations:
            name = relation.name
            if needle in name.casefold():
                found.append(CatalogMatch(kind=CatalogMatchKind_Relation(), relation=name, name=name, ordinal=0))
                if len(found) >= maximum_matches:
                    break
    return Ok(value=CottList(values=found))
