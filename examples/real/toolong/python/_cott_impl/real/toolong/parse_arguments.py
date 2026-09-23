from pathlib import Path

from cott_runtime import CottList, Err, Nothing, Ok, Option, Result, Some
from real.toolong_types import ToolongError, ToolongError_InvalidArguments, ViewerOptions


def parse_arguments(arguments: CottList[str]) -> Result[ViewerOptions, ToolongError]:
    contains: Option[str] = Nothing()
    expecting_text: bool = False
    first: bool = True
    sources: list[Path] = []
    for argument in arguments:
        if expecting_text:
            contains = Some(value=argument)
            expecting_text = False
        elif first and argument == "--contains":
            expecting_text = True
        else:
            sources.append(Path(argument))
        first = False
    if expecting_text:
        return Err(error=ToolongError_InvalidArguments(message="--contains requires TEXT"))
    if len(sources) == 0:
        return Err(error=ToolongError_InvalidArguments(message="at least one log path is required"))
    return Ok(value=ViewerOptions(sources=CottList(values=sources), contains=contains))
