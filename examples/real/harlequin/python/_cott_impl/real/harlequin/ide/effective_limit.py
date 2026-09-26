from typing import Final

from cott_runtime import U64, Nothing, Option, Some

from real.harlequin.ide_types import RunBar

_U64_MAX: Final[int] = 18446744073709551615


def effective_limit(bar: RunBar) -> Option[U64]:
    text = bar.limit_text
    if bar.limit_enabled and text != "" and text.isascii() and text.isdigit():
        digits = text.lstrip("0") or "0"
        if len(digits) <= len(str(_U64_MAX)):
            value = int(digits)
            if value <= _U64_MAX:
                return Some(value=value)
    return Nothing()
