from typing import Final

from cott_runtime import CottList, Some, U64
from wcwidth import wcwidth

from real.harlequin.ide_types import Notification, Severity_Error, Severity_Warning
from real.harlequin.style_types import StyledLine, StyledSpan

_PREFIX: Final[str] = "▌ "
_MAX_SHOWN: Final[int] = 3


def _cell_width(ch: str) -> int:
    w = wcwidth(ch)
    return w if w > 0 else 0


def _text_width(text: str) -> int:
    return sum(_cell_width(ch) for ch in text)


def _hard_wrap(word: str, limit: int) -> list[str]:
    out: list[str] = []
    cur = ""
    cur_w = 0
    for ch in word:
        w = _cell_width(ch)
        if cur and cur_w + w > limit:
            out.append(cur)
            cur = ""
            cur_w = 0
        cur += ch
        cur_w += w
    out.append(cur)
    return out


def _wrap(text: str, limit: int) -> list[str]:
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        cur = ""
        cur_w = 0
        for word in raw.split(" "):
            ww = _text_width(word)
            if cur_w == 0 and not cur:
                if ww <= limit:
                    cur, cur_w = word, ww
                else:
                    pieces = _hard_wrap(word, limit)
                    lines.extend(pieces[:-1])
                    cur, cur_w = pieces[-1], _text_width(pieces[-1])
            elif cur_w + 1 + ww <= limit:
                cur += " " + word
                cur_w += 1 + ww
            else:
                lines.append(cur)
                if ww <= limit:
                    cur, cur_w = word, ww
                else:
                    pieces = _hard_wrap(word, limit)
                    lines.extend(pieces[:-1])
                    cur, cur_w = pieces[-1], _text_width(pieces[-1])
        lines.append(cur)
    return lines


def _line(prefix_style: str, style: str, text: str) -> StyledLine:
    return StyledLine(spans=CottList(values=[StyledSpan(style=prefix_style, text=_PREFIX), StyledSpan(style=style, text=text)]))


def render_notifications(notifications: CottList[Notification], now_ms: U64, width: U64) -> CottList[StyledLine]:
    live: list[Notification] = [n for n in notifications if n.expires_at_ms > now_ms]
    shown = live[-_MAX_SHOWN:]
    limit = max(1, width - 2)
    out: list[StyledLine] = []
    for index, note in enumerate(shown):
        if index > 0:
            out.append(StyledLine(spans=CottList(values=[])))
        severity = note.severity
        if isinstance(severity, Severity_Error):
            prefix_style = "class:hq.notification.error"
            body_style = "class:hq.notification.error"
        elif isinstance(severity, Severity_Warning):
            prefix_style = "class:hq.warning"
            body_style = "class:hq.notification"
        else:
            prefix_style = "class:hq.notification"
            body_style = "class:hq.notification"
        title = note.title
        if isinstance(title, Some):
            for text in _wrap(title.value, limit):
                out.append(_line(prefix_style, body_style + " class:hq.dialog.title", text))
        for text in _wrap(note.message, limit):
            out.append(_line(prefix_style, body_style, text))
    return CottList(values=out)
