from typing import cast

from cott_runtime import Opaque
from real.pgcli.completion_types import PrevalenceHandle


def clear_prevalence_names(prevalence: PrevalenceHandle) -> PrevalenceHandle:
    data = cast(dict[str, dict[str, int]], prevalence.unwrap())
    return Opaque(tag="pgcli.prevalence", value={"keywords": dict(data["keywords"]), "names": {}})
