from typing import cast

from cott_runtime import FrozenMap, U64
from real.pgcli.completion_types import Prevalence, PrevalenceHandle


def _counts(value: object) -> FrozenMap[str, U64]:
    if not isinstance(value, dict):
        raise TypeError("Invalid prevalence counts")
    counts: dict[str, U64] = {}
    for key, count in cast(dict[object, object], value).items():
        if not isinstance(key, str) or not isinstance(count, int) or isinstance(count, bool) or not 0 <= count < 2**64:
            raise TypeError("Invalid prevalence counts")
        counts[key] = count
    return FrozenMap(values=counts)


def prevalence_counts(prevalence: PrevalenceHandle) -> Prevalence:
    payload = prevalence.unwrap()
    if not isinstance(payload, dict):
        raise TypeError("Invalid prevalence payload")
    data = cast(dict[object, object], payload)
    return Prevalence(keyword_counts=_counts(data.get("keywords")), name_counts=_counts(data.get("names")))
