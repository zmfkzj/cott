from typing import Literal, cast

from cott_runtime import Opaque

from real.harlequin.catalog_types import Completion


def _payload(handle: Opaque[Literal["harlequin.completions"]]) -> tuple[Completion, ...]:
    if handle.tag != "harlequin.completions":
        raise TypeError("expected a harlequin.completions handle")
    return cast(tuple[Completion, ...], handle.unwrap())


def join_completion_sets(first: Opaque[Literal["harlequin.completions"]], second: Opaque[Literal["harlequin.completions"]]) -> Opaque[Literal["harlequin.completions"]]:
    return Opaque(tag="harlequin.completions", value=_payload(first) + _payload(second))
