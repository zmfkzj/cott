from cott_runtime import CottList


def parse_destructive_warning(values: CottList[str]) -> CottList[str]:
    items: list[str] = [value for value in values]
    if len(items) == 0:
        return CottList(values=[])
    first = items[0]
    if len(items) == 1 and "," in first:
        return CottList(values=first.split(","))
    if first in ("true", "all"):
        return CottList(values=["drop", "shutdown", "delete", "truncate", "alter", "unconditional_update", "update"])
    if first == "moderate":
        return CottList(values=["drop", "shutdown", "delete", "truncate", "alter", "unconditional_update"])
    if first in ("false", "off", ""):
        return CottList(values=[])
    return CottList(values=items)
