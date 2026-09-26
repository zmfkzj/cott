import dataclasses

from cott_runtime import CottList, Some

from real.harlequin.catalog_types import CatalogEntry


def normalize_catalog(entries: CottList[CatalogEntry]) -> CottList[CatalogEntry]:
    kept: dict[str, CatalogEntry] = {}
    children: dict[str, list[str]] = {}
    roots: list[str] = []
    for entry in entries:
        if entry.id in kept:
            continue
        parent = entry.parent
        if isinstance(parent, Some):
            if parent.value not in kept:
                continue
            children[parent.value].append(entry.id)
        else:
            roots.append(entry.id)
        kept[entry.id] = entry
        children[entry.id] = []
    result: list[CatalogEntry] = []
    stack: list[tuple[str, int]] = [(root, 0) for root in reversed(roots)]
    while stack:
        node_id, depth = stack.pop()
        entry = kept[node_id]
        kids = children[node_id]
        has_kids = len(kids) > 0
        expandable = True if has_kids else entry.expandable
        loaded = True if has_kids else entry.loaded
        if entry.depth != depth or entry.expandable != expandable or entry.loaded != loaded:
            entry = dataclasses.replace(entry, depth=depth, expandable=expandable, loaded=loaded)
        result.append(entry)
        for kid in reversed(kids):
            stack.append((kid, depth + 1))
    return CottList(values=result)
