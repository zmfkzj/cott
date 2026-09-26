from cott_runtime import CottList, U64
from frogmouth.bookmarks_types import Bookmark


def delete_bookmark(bookmarks: CottList[Bookmark], index: U64) -> CottList[Bookmark]:
    items = list(bookmarks)
    return CottList(values=items[:index] + items[index + 1:])
