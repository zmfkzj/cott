from cott_runtime import CottList
from rich.markup import escape

from frogmouth.bookmarks_types import Bookmark
from frogmouth.model_types import LocationKind_Local


def bookmark_entries(bookmarks: CottList[Bookmark]) -> CottList[str]:
    entries: list[str] = []
    for bookmark in bookmarks:
        icon = ":page_facing_up:" if isinstance(bookmark.location.kind, LocationKind_Local) else ":globe_with_meridians:"
        entries.append(f"{icon} [bold]{escape(bookmark.title)}[/]\n[dim]{escape(bookmark.location.target)}[/]")
    return CottList(values=entries)
