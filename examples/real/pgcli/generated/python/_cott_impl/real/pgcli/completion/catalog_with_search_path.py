from typing import Literal, cast

from cott_runtime import CottList, Opaque


def catalog_with_search_path(catalog: Opaque[Literal["pgcli.completion-catalog"]], search_path: CottList[str]) -> Opaque[Literal["pgcli.completion-catalog"]]:
    data = dict(cast(dict[str, object], catalog.unwrap()))
    data["search_path"] = [s for s in search_path]
    return Opaque(tag="pgcli.completion-catalog", value=data)
