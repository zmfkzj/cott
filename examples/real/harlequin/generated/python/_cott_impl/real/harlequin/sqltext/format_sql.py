from typing import Any, cast

import sqlfmt.api
import sqlfmt.exception
import sqlfmt.mode
from cott_runtime import Err, Ok, Result

from real.harlequin.sqltext_types import FormatError, FormatError_Unformattable


def format_sql(text: str) -> Result[str, FormatError]:
    api: Any = sqlfmt.api
    mode_module: Any = sqlfmt.mode
    exception_module: Any = sqlfmt.exception
    error_type = cast(type[BaseException], exception_module.SqlfmtError)
    try:
        formatted = cast(object, api.format_string(text, mode_module.Mode()))
    except error_type as error:
        return _unformattable(str(error))
    if not isinstance(formatted, str):
        return _unformattable("sqlfmt returned a non-string result")
    return Ok(value=formatted)


def _unformattable(message: str) -> Result[str, FormatError]:
    return Err(error=FormatError_Unformattable(message=message))
