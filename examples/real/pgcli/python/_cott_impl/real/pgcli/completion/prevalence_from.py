from typing import Literal

from cott_runtime import FrozenMap, Opaque, U64


def prevalence_from(keyword_counts: FrozenMap[str, U64], name_counts: FrozenMap[str, U64]) -> Opaque[Literal["pgcli.prevalence"]]:
    keywords: dict[str, int] = {key: int(count) for key, count in keyword_counts.items()}
    names: dict[str, int] = {key: int(count) for key, count in name_counts.items()}
    return Opaque(tag="pgcli.prevalence", value={"keywords": keywords, "names": names})
