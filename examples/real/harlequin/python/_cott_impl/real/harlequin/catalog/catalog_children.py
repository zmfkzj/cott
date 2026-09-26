from cott_runtime import CottList, Nothing, Some

from real.harlequin.catalog_types import CatalogEntry


def catalog_children(catalog: CottList[CatalogEntry], parent: Some[str] | Nothing) -> CottList[CatalogEntry]:
    wanted: str | None = parent.value if isinstance(parent, Some) else None
    result: list[CatalogEntry] = []
    for entry in catalog:
        entry_parent = entry.parent
        if isinstance(entry_parent, Some):
            if wanted is not None and entry_parent.value == wanted:
                result.append(entry)
        elif wanted is None:
            result.append(entry)
    return CottList(values=result)
