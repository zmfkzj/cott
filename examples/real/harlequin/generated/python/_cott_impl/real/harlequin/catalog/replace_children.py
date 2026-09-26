from cott_runtime import CottList, Some

from real.harlequin.catalog_types import CatalogEntry


def _with_position(entry: CatalogEntry, parent: str, depth: int) -> CatalogEntry:
    return CatalogEntry(id=entry.id, parent=Some(value=parent), depth=depth, label=entry.label, type_label=entry.type_label, kind=entry.kind, qualified_identifier=entry.qualified_identifier, query_name=entry.query_name, expandable=entry.expandable, loaded=entry.loaded)


def _parent_id(entry: CatalogEntry) -> str | None:
    value = entry.parent
    if isinstance(value, Some):
        return value.value
    return None


def replace_children(catalog: CottList[CatalogEntry], parent: str, children: CottList[CatalogEntry]) -> CottList[CatalogEntry]:
    entries: list[CatalogEntry] = [entry for entry in catalog]
    target: CatalogEntry | None = None
    for entry in entries:
        if entry.id == parent:
            target = entry
            break
    if target is None:
        return catalog
    removed: set[str] = set()
    changed = True
    while changed:
        changed = False
        for entry in entries:
            pid = _parent_id(entry)
            if entry.id not in removed and entry.id != parent and pid is not None and (pid == parent or pid in removed):
                removed.add(entry.id)
                changed = True
    outside: set[str] = {entry.id for entry in entries if entry.id not in removed}
    depths: dict[str, int] = {}
    roots: dict[str, str] = {}
    tops: list[CatalogEntry] = []
    groups: dict[str, list[CatalogEntry]] = {}
    for child in children:
        pid = _parent_id(child)
        if pid is None or child.id in outside or child.id in depths:
            continue
        if pid == parent:
            depths[child.id] = target.depth + 1
            roots[child.id] = child.id
            placed = _with_position(child, parent, target.depth + 1)
            tops.append(placed)
            groups[child.id] = []
        elif pid in depths:
            depth = depths[pid] + 1
            depths[child.id] = depth
            root = roots[pid]
            roots[child.id] = root
            groups[root].append(_with_position(child, pid, depth))
    tops.sort(key=lambda entry: (entry.label.casefold(), entry.label))
    new_parent = CatalogEntry(id=target.id, parent=target.parent, depth=target.depth, label=target.label, type_label=target.type_label, kind=target.kind, qualified_identifier=target.qualified_identifier, query_name=target.query_name, expandable=True, loaded=True)
    result: list[CatalogEntry] = []
    for entry in entries:
        if entry.id in removed:
            continue
        if entry.id == parent:
            result.append(new_parent)
            for top in tops:
                result.append(top)
                result.extend(groups[top.id])
        else:
            result.append(entry)
    return CottList(values=result)
