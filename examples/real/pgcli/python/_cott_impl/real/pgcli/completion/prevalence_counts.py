from typing import cast

from cott_runtime import FrozenMap, U64

from real.pgcli.completion_types import Prevalence, PrevalenceHandle


def _counts(value: object) -> dict[str, U64]:
    result: dict[str, U64] = {}
    if isinstance(value, dict):
        for key, count in cast(dict[object, object], value).items():
            if isinstance(key, str) and isinstance(count, int) and not isinstance(count, bool):
                result[key] = count
    return result


def prevalence_counts(prevalence: PrevalenceHandle) -> Prevalence:
    data = prevalence.unwrap()
    keywords: object = None
    names: object = None
    if isinstance(data, dict):
        payload = cast(dict[object, object], data)
        keywords = payload.get("keywords")
        names = payload.get("names")
    return Prevalence(keyword_counts=FrozenMap(values=_counts(keywords)), name_counts=FrozenMap(values=_counts(names)))
