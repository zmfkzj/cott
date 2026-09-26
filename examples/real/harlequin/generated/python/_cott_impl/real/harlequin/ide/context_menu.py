from cott_runtime import CottList

from real.harlequin.catalog_types import CatalogEntry
from real.harlequin.ide_types import ContextMenu


def context_menu(entry: CatalogEntry, interactions: CottList[str]) -> ContextMenu:
    items = ["Insert Name at Cursor"]
    for item in interactions:
        items.append(item)
    return ContextMenu(entry=entry, items=CottList(values=items), selected=0)
