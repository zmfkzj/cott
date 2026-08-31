from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import (
    CliInput,
    InputKind_Argument,
    InputKind_BatchFile,
    InputKind_ConfigFile,
    MediaError,
    MediaError_InvalidInput,
)


def resolve_inputs(inputs: CottList[CliInput], config: CottList[CliInput]) -> Result[CottList[str], MediaError]:
    urls: list[str] = []
    item: CliInput
    for item in config:
        if item.value == "":
            return Err(error=MediaError_InvalidInput(message="input values must not be empty"))
        match item.kind:
            case InputKind_Argument():
                urls.append(item.value)
            case InputKind_ConfigFile() | InputKind_BatchFile():
                continue

    for item in inputs:
        if item.value == "":
            return Err(error=MediaError_InvalidInput(message="input values must not be empty"))
        match item.kind:
            case InputKind_Argument():
                urls.append(item.value)
            case InputKind_ConfigFile() | InputKind_BatchFile():
                continue

    if len(urls) == 0:
        return Err(error=MediaError_InvalidInput(message="no URLs were provided"))
    return Ok(value=CottList(values=tuple(urls)))
