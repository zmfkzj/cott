import re

from cott_runtime import CottList


def change_db_arguments(pattern: str) -> CottList[str]:
    items: list[str] = [match.group(0) for match in re.finditer(r'"[^"]*"|[^"\'\s]+', pattern)]
    while len(items) < 4:
        items.append("")
    return CottList(values=items)
