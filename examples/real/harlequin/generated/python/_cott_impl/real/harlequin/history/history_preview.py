from typing import Final

from cott_runtime import CottList

_MAX_LINES: Final[int] = 8
_SHOWN_LINES: Final[int] = 7


def history_preview(sql: str) -> CottList[str]:
    lines = sql.strip().splitlines()
    if len(lines) > _MAX_LINES:
        hidden = len(lines) - _SHOWN_LINES
        lines = lines[:_SHOWN_LINES] + [f"… ({hidden} more lines)"]
    return CottList(values=lines)
