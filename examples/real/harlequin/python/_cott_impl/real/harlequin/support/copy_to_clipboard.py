from typing import Any

import pyperclip
from cott_runtime import UNIT, Err, Ok, Result, Unit

from real.harlequin.support_types import ClipboardError, ClipboardError_Unavailable


def copy_to_clipboard(text: str) -> Result[Unit, ClipboardError]:
    clip: Any = pyperclip
    try:
        clip.copy(text)
    except pyperclip.PyperclipException as exc:
        return Err(error=ClipboardError_Unavailable(message=str(exc)))
    return Ok(value=UNIT)
