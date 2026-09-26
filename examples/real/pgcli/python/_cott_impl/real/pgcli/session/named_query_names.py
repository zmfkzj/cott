from typing import Any, Literal, cast

from cott_runtime import CottList, Opaque
from pgspecial.namedqueries import NamedQueries


def named_query_names(special: Opaque[Literal["pgcli.pgspecial"]]) -> CottList[str]:
    del special
    queries: Any = NamedQueries.instance
    raw = cast(object, queries.list())
    items: list[object]
    if isinstance(raw, dict):
        items = list(cast(dict[object, object], raw).keys())
    elif isinstance(raw, list):
        items = cast(list[object], raw)
    else:
        raise TypeError("NamedQueries.list() returned an unexpected type")
    names: list[str] = []
    for item in items:
        if not isinstance(item, str):
            raise TypeError("named query name is not str")
        names.append(item)
    return CottList(values=names)
