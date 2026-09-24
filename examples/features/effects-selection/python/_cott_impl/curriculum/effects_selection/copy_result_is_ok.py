from cott_runtime import U64, Ok, Result
from curriculum.effects_selection_types import EffectError


def copy_result_is_ok(result: Result[U64, EffectError]) -> bool:
    return isinstance(result, Ok)
