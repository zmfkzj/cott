from cott_runtime import CottList
from frogmouth.bookmarks_types import Bookmark
from frogmouth.model_types import Location


def add_bookmark(bookmarks: CottList[Bookmark], title: str, location: Location) -> CottList[Bookmark]:
    items: list[Bookmark] = list(bookmarks)
    items.append(Bookmark(title=title, location=location))
    result: list[Bookmark] = []
    for item in items:
        position: int = len(result)
        while position > 0 and result[position - 1].title > item.title:
            position -= 1
        result.insert(position, item)
    return CottList(values=result)
