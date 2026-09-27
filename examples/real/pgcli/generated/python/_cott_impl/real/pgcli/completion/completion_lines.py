from typing import cast

from cott_runtime import CottList, U64
from prompt_toolkit.completion import Completion

from real.pgcli.completion_types import CompletionList


def completion_lines(completions: CompletionList, limit: U64) -> CottList[str]:
    items = cast(list[Completion], completions.unwrap())
    lines: list[str] = []
    for item in items[:limit]:
        lines.append(item.text + " | " + str(item.start_position) + " | " + item.display_text + " | " + item.display_meta_text)
    return CottList(values=lines)
