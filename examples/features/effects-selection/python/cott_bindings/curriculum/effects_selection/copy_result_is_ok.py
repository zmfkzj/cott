from __future__ import annotations

from cott_runtime import Ok, Result, U64
from curriculum.effects_selection_types import EffectError


def copy_result_is_ok(result: Result[U64, EffectError]) -> bool:
    return isinstance(result, Ok)
