from cott_runtime import CottList, Some

from real.harlequin.catalog_types import CatalogEntry, TreeState


def visible_entries(catalog: CottList[CatalogEntry], tree: TreeState) -> CottList[CatalogEntry]:
    expanded: set[str] = {item for item in tree.expanded}
    children: dict[str, list[CatalogEntry]] = {}
    roots: list[CatalogEntry] = []
    for entry in catalog:
        parent = entry.parent
        if isinstance(parent, Some):
            children.setdefault(parent.value, []).append(entry)
        else:
            roots.append(entry)
    result: list[CatalogEntry] = []
    stack: list[CatalogEntry] = list(reversed(roots))
    while stack:
        entry = stack.pop()
        result.append(entry)
        if entry.id in expanded:
            stack.extend(reversed(children.get(entry.id, [])))
    return CottList(values=result)
