from typing import Literal, cast

from cott_runtime import CottList, Opaque, U64
from prompt_toolkit.completion import Completion

from real.pgcli.completion_types import CompletionItem


def completion_items(completions: Opaque[Literal["pgcli.completions"]], limit: U64) -> CottList[CompletionItem]:
    items = cast(list[Completion], completions.unwrap())
    return CottList(values=[CompletionItem(text=c.text, start_position=c.start_position, display=c.display_text, display_meta=c.display_meta_text) for c in items[:limit]])
