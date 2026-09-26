from cott_runtime import CottList, Nothing, Option, Some

from real.harlequin.catalog_types import CatalogEntry, TreeState


def _visible_rows(catalog: CottList[CatalogEntry], tree: TreeState) -> list[CatalogEntry]:
    expanded: set[str] = set(tree.expanded)
    ids: set[str] = {entry.id for entry in catalog}
    children: dict[str, list[CatalogEntry]] = {}
    roots: list[CatalogEntry] = []
    for entry in catalog:
        parent = entry.parent
        if isinstance(parent, Some) and parent.value in ids:
            children.setdefault(parent.value, []).append(entry)
        else:
            roots.append(entry)
    rows: list[CatalogEntry] = []
    seen: set[str] = set()
    stack: list[CatalogEntry] = list(reversed(roots))
    while stack:
        entry = stack.pop()
        if entry.id in seen:
            continue
        seen.add(entry.id)
        rows.append(entry)
        if entry.id in expanded:
            stack.extend(reversed(children.get(entry.id, [])))
    return rows


def tree_cursor_entry(catalog: CottList[CatalogEntry], tree: TreeState) -> Option[CatalogEntry]:
    rows = _visible_rows(catalog, tree)
    if tree.cursor < len(rows):
        return Some(value=rows[tree.cursor])
    return Nothing()
