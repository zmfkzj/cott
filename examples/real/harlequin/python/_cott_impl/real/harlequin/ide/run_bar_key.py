from real.harlequin.ide_types import RunBar, RunBarStep


def _valid(text: str) -> bool:
    return text != "" and text.isascii() and text.isdigit()


def _edited(bar: RunBar, text: str, cursor: int) -> RunBarStep:
    return RunBarStep(bar=RunBar(limit_enabled=_valid(text), limit_text=text, limit_cursor=cursor, running=bar.running), submit=False)


def run_bar_key(bar: RunBar, key: str, text: str) -> RunBarStep:
    current = bar.limit_text
    cursor = min(bar.limit_cursor, len(current))
    if key == "space":
        enabled = False if bar.limit_enabled else _valid(current)
        return RunBarStep(bar=RunBar(limit_enabled=enabled, limit_text=current, limit_cursor=bar.limit_cursor, running=bar.running), submit=False)
    if len(key) == 1 and key.isascii() and key.isdigit():
        return _edited(bar, current[:cursor] + key + current[cursor:], cursor + 1)
    if key == "backspace":
        if cursor == 0:
            return _edited(bar, current, cursor)
        return _edited(bar, current[: cursor - 1] + current[cursor:], cursor - 1)
    if key == "delete":
        return _edited(bar, current[:cursor] + current[cursor + 1 :], cursor)
    moved = bar.limit_cursor
    if key == "left":
        moved = max(cursor - 1, 0)
    elif key == "right":
        moved = min(cursor + 1, len(current))
    elif key == "home":
        moved = 0
    elif key == "end":
        moved = len(current)
    elif key == "enter":
        return RunBarStep(bar=bar, submit=_valid(current))
    else:
        return RunBarStep(bar=bar, submit=False)
    return RunBarStep(bar=RunBar(limit_enabled=bar.limit_enabled, limit_text=current, limit_cursor=moved, running=bar.running), submit=False)
