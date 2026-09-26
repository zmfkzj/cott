import re

from cott_runtime import Nothing, Option, Some
from real.toolong.text_types import CompletionTarget, SEARCH_SPLIT_PATTERN


def completion_target(value: str) -> Option[CompletionTarget]:
    word = re.split(SEARCH_SPLIT_PATTERN, value)[-1]
    if word == "":
        return Nothing()
    return Some(value=CompletionTarget(start=value[: len(value) - len(word)], word=word))
