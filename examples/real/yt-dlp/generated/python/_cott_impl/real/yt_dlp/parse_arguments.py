from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import (
    CliInput,
    InputKind_Argument,
    InputKind_BatchFile,
    InputKind_ConfigFile,
    MediaError,
    MediaError_InvalidInput,
)


def parse_arguments(arguments: CottList[str]) -> Result[CottList[CliInput], MediaError]:
    inputs: list[CliInput] = []
    positional_only: bool = False
    index: int = 0
    while index < len(arguments):
        argument: str = arguments[index]
        if argument == "":
            return Err(error=MediaError_InvalidInput(message="arguments must not be empty"))
        if positional_only:
            inputs.append(CliInput(kind=InputKind_Argument(), value=argument))
            index += 1
            continue
        if argument == "--":
            positional_only = True
            index += 1
            continue

        kind: InputKind_Argument | InputKind_BatchFile | InputKind_ConfigFile
        value: str
        if argument == "--config-locations":
            index += 1
            if index == len(arguments) or arguments[index] == "":
                return Err(error=MediaError_InvalidInput(message=f"{argument} requires a path"))
            kind = InputKind_ConfigFile()
            value = arguments[index]
        elif argument.startswith("--config-locations="):
            value = argument.partition("=")[2]
            if value == "":
                return Err(error=MediaError_InvalidInput(message="--config-locations requires a path"))
            kind = InputKind_ConfigFile()
        elif argument in ("-a", "--batch-file"):
            index += 1
            if index == len(arguments) or arguments[index] == "":
                return Err(error=MediaError_InvalidInput(message=f"{argument} requires a path"))
            kind = InputKind_BatchFile()
            value = arguments[index]
        elif argument.startswith("--batch-file="):
            value = argument.partition("=")[2]
            if value == "":
                return Err(error=MediaError_InvalidInput(message="--batch-file requires a path"))
            kind = InputKind_BatchFile()
        elif argument.startswith("-a") and len(argument) > 2:
            kind = InputKind_BatchFile()
            value = argument[2:]
        else:
            kind = InputKind_Argument()
            value = argument
        inputs.append(CliInput(kind=kind, value=value))
        index += 1
    return Ok(value=CottList(values=tuple(inputs)))
