from typing import Any, cast

import pyperclip
from cott_runtime import Err, Ok, Result
from real.harlequin.support_types import ClipboardError, ClipboardError_Unavailable


def paste_from_clipboard() -> Result[str, ClipboardError]:
    clipboard: Any = pyperclip
    try:
        pasted = cast(object, clipboard.paste())
    except Exception as exc:
        return Err(error=ClipboardError_Unavailable(message=str(exc)))
    if not isinstance(pasted, str):
        return Err(error=ClipboardError_Unavailable(message="Clipboard did not return text."))
    return Ok(value=pasted)
