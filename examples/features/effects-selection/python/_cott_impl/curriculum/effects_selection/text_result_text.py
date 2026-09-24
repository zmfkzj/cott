from cott_runtime import Ok, Result

from curriculum.effects_selection_types import EffectError


def text_result_text(result: Result[str, EffectError]) -> str:
    if isinstance(result, Ok):
        return result.value
    return ""
