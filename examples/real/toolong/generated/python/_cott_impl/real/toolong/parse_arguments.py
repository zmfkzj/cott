from pathlib import Path

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.toolong_types import ToolongError, ToolongError_InvalidArguments, ViewerOptions


def parse_arguments(arguments: CottList[str]) -> Result[ViewerOptions, ToolongError]:
    if len(arguments) == 0:
        return Err(error=ToolongError_InvalidArguments(message="expected at least one log path"))
    if arguments[0] == "--contains":
        if len(arguments) < 3:
            return Err(
                error=ToolongError_InvalidArguments(
                    message="--contains requires text and at least one log path"
                )
            )
        return Ok(
            value=ViewerOptions(
                sources=CottList(values=tuple(Path(argument) for argument in arguments[2:])),
                contains=Some(value=arguments[1]),
            )
        )
    return Ok(
        value=ViewerOptions(
            sources=CottList(values=tuple(Path(argument) for argument in arguments)),
            contains=Nothing(),
        )
    )
