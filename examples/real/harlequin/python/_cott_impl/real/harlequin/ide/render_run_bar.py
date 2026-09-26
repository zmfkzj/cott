from typing import Final

from cott_runtime import U16, CottList, Option, Some
from wcwidth import wcwidth

from real.harlequin.adapters_types import TransactionMode
from real.harlequin.ide_types import RunBar
from real.harlequin.style_types import StyledLine, StyledSpan

_STATUS: Final[str] = "class:hq.status"


def _cells(text: str) -> int:
    total = 0
    for ch in text:
        w = wcwidth(ch)
        total += w if w > 0 else 0
    return total


def _cut(text: str, limit: int) -> str:
    out: list[str] = []
    used = 0
    for ch in text:
        w = wcwidth(ch)
        w = w if w > 0 else 0
        if used + w > limit:
            break
        out.append(ch)
        used += w
    return "".join(out)


def render_run_bar(bar: RunBar, transaction: Option[TransactionMode], can_cancel: bool, run_label: str, runnable: bool, focused: bool, width: U16) -> StyledLine:
    left: list[tuple[str, str]] = []
    if isinstance(transaction, Some):
        tx = transaction.value
        text = f"[Tx: {tx.label}]"
        if tx.can_commit:
            text += " [🡅]"
        if tx.can_rollback:
            text += " [⮌]"
        left.append((_STATUS, text + " "))
    left.append((_STATUS, "[x] Limit " if bar.limit_enabled else "[ ] Limit "))
    limit_text = bar.limit_text + " " * max(0, 7 - _cells(bar.limit_text))
    left.append(("class:hq.input class:hq.cursor" if focused else "class:hq.input", limit_text))
    if bar.running and can_cancel:
        button = ("class:hq.button.focused", "[ Cancel Query ]")
    elif bar.running:
        button = ("class:hq.loading", "[ Running... ]")
    else:
        button = ("class:hq.button" if runnable else "class:hq.muted", f"[ {run_label} ]")
    used = sum(_cells(t) for _, t in left) + _cells(button[1])
    gap = max(0, width - used)
    parts = left + [(_STATUS, " " * gap), button]
    spans: list[StyledSpan] = []
    remaining = width
    for style, text in parts:
        if remaining <= 0:
            break
        piece = _cut(text, remaining)
        remaining -= _cells(piece)
        if piece:
            spans.append(StyledSpan(style=style, text=piece))
    if remaining > 0:
        spans.append(StyledSpan(style=_STATUS, text=" " * remaining))
    return StyledLine(spans=CottList(values=spans))
