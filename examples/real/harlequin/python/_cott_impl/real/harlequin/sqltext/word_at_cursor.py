from cott_runtime import U64
from real.harlequin.sqltext_types import TextRange


def _is_word_char(ch: str) -> bool:
    return ch.isalnum() or ch in '_$."'


def word_at_cursor(text: str, cursor: U64) -> TextRange:
    end = min(cursor, len(text))
    start = end
    while start > 0 and _is_word_char(text[start - 1]):
        start -= 1
    return TextRange(start=start, end=end)
