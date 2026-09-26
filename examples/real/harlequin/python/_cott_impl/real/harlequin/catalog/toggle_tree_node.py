from cott_runtime import CottList, Nothing, Some

from real.harlequin.catalog import visible_entries
from real.harlequin.catalog_types import CatalogEntry, TreeState, TreeToggle


def toggle_tree_node(catalog: CottList[CatalogEntry], tree: TreeState) -> TreeToggle:
    unchanged = TreeToggle(tree=tree, load_children=Nothing())
    rows = visible_entries(catalog, tree)
    if len(rows) == 0 or tree.cursor >= len(rows):
        return unchanged
    entry = rows[tree.cursor]
    if not entry.expandable:
        return unchanged
    expanded: list[str] = [node for node in tree.expanded]
    if entry.id in expanded:
        remaining: list[str] = [node for node in expanded if node != entry.id]
        new_tree = TreeState(expanded=CottList(values=remaining), cursor=tree.cursor, first_row=tree.first_row)
        return TreeToggle(tree=new_tree, load_children=Nothing())
    expanded.append(entry.id)
    new_tree = TreeState(expanded=CottList(values=expanded), cursor=tree.cursor, first_row=tree.first_row)
    load: Some[str] | Nothing = Nothing() if entry.loaded else Some(value=entry.id)
    return TreeToggle(tree=new_tree, load_children=load)
