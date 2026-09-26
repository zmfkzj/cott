from typing import cast

from cott_runtime import U64, CottList
from prompt_toolkit.completion import Completion

from real.pgcli.completion_types import CompletionList


def completion_lines(completions: CompletionList, limit: U64) -> CottList[str]:
    items = cast(list[Completion], completions.unwrap())
    lines: list[str] = []
    for c in items[:limit]:
        lines.append(c.text + " | " + str(c.start_position) + " | " + c.display_text + " | " + c.display_meta_text)
    return CottList(values=lines)
