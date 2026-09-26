from cott_runtime import CottList, U64
from frogmouth.bookmarks_types import Bookmark


def rename_bookmark(bookmarks: CottList[Bookmark], index: U64, title: str) -> CottList[Bookmark]:
    items: list[Bookmark] = list(bookmarks)
    items[index] = Bookmark(title=title, location=items[index].location)
    return CottList(values=items)
