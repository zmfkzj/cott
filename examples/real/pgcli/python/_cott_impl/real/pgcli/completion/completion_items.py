from typing import Literal, cast

from cott_runtime import CottList, Opaque, U64
from prompt_toolkit.completion import Completion

from real.pgcli.completion_types import CompletionItem


def completion_items(completions: Opaque[Literal["pgcli.completions"]], limit: U64) -> CottList[CompletionItem]:
    raw = completions.unwrap()
    if not isinstance(raw, list):
        raise TypeError("completion payload must be a list")

    result: list[CompletionItem] = []
    for item in cast(list[object], raw)[:limit]:
        if not isinstance(item, Completion):
            raise TypeError("completion payload contains a non-Completion value")
        result.append(CompletionItem(text=item.text, start_position=item.start_position, display=item.display_text, display_meta=item.display_meta_text))
    return CottList(values=result)
