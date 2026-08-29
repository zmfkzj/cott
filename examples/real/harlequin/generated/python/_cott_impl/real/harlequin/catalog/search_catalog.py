from cott_runtime import CottList, Err, Ok, Result
from real.harlequin.catalog import catalog_columns, catalog_relations
from real.harlequin.catalog_types import CatalogMatch, CatalogMatchKind_Column, CatalogMatchKind_Relation
from real.harlequin.core_types import DatabaseTarget, SqlClientError


def search_catalog(database: DatabaseTarget, term: str) -> Result[CottList[CatalogMatch], SqlClientError]:
    folded_term = term.casefold()
    matches: list[CatalogMatch] = []

    match catalog_relations(database):
        case Err(error=error):
            return Err(error=error)
        case Ok(value=relations):
            for relation in relations:
                if folded_term in relation.name.casefold():
                    matches.append(
                        CatalogMatch(
                            kind=CatalogMatchKind_Relation(),
                            relation=relation.name,
                            name=relation.name,
                            ordinal=0,
                        )
                    )
                    if len(matches) == 1000:
                        return Ok(value=CottList(values=tuple(matches)))

                match catalog_columns(database, relation.name):
                    case Err(error=error):
                        return Err(error=error)
                    case Ok(value=columns):
                        for column in columns:
                            if folded_term in column.name.casefold():
                                matches.append(
                                    CatalogMatch(
                                        kind=CatalogMatchKind_Column(),
                                        relation=relation.name,
                                        name=column.name,
                                        ordinal=column.ordinal,
                                    )
                                )
                                if len(matches) == 1000:
                                    return Ok(value=CottList(values=tuple(matches)))

    return Ok(value=CottList(values=tuple(matches)))
