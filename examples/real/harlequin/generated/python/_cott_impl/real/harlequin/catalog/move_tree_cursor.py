from cott_runtime import CottList, Some, U64

from real.harlequin.catalog import visible_entries
from real.harlequin.catalog_types import CatalogEntry, TreeMotion, TreeMotion_Down, TreeMotion_First, TreeMotion_Last, TreeMotion_PageDown, TreeMotion_PageUp, TreeMotion_Up, TreeState


def move_tree_cursor(catalog: CottList[CatalogEntry], tree: TreeState, motion: TreeMotion, page_rows: U64) -> TreeState:
    rows = visible_entries(catalog, tree)
    count = len(rows)
    if count == 0:
        return TreeState(expanded=tree.expanded, cursor=0, first_row=tree.first_row)
    last = count - 1
    current = min(tree.cursor, last)
    page = max(page_rows, 1)
    target = current
    if isinstance(motion, TreeMotion_Up):
        target = current - 1
    elif isinstance(motion, TreeMotion_Down):
        target = current + 1
    elif isinstance(motion, TreeMotion_PageUp):
        target = current - page
    elif isinstance(motion, TreeMotion_PageDown):
        target = current + page
    elif isinstance(motion, TreeMotion_First):
        target = 0
    elif isinstance(motion, TreeMotion_Last):
        target = last
    else:
        parent = rows[current].parent
        if isinstance(parent, Some):
            parent_id = parent.value
            index = 0
            for row in rows:
                if row.id == parent_id:
                    target = index
                    break
                index += 1
    target = max(0, min(target, last))
    return TreeState(expanded=tree.expanded, cursor=target, first_row=tree.first_row)
