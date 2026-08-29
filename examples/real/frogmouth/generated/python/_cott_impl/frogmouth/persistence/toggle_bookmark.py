from cott_runtime import CottList


def toggle_bookmark(bookmarks: CottList[str], location: str) -> CottList[str]:
    remaining: list[str] = []
    found = False
    for bookmark in bookmarks:
        if bookmark == location:
            found = True
        else:
            remaining.append(bookmark)
    if not found:
        remaining.append(location)
    return CottList(values=remaining)
