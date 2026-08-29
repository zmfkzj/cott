from __future__ import annotations

from cott_runtime import Ok, Result
from curriculum.effects_selection_types import EffectError


def text_result_is_ok(result: Result[str, EffectError]) -> bool:
    return isinstance(result, Ok)
