from typing import Literal

from cott_runtime import CottList, Opaque

from real.harlequin.catalog_types import Completion


def completion_set(completions: CottList[Completion]) -> Opaque[Literal["harlequin.completions"]]:
    return Opaque(tag="harlequin.completions", value=tuple(completions))
