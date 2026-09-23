from cott_runtime import CottList, Err, Ok, Result
from real.yt_dlp_types import CliInput, InputKind, InputKind_Argument, InputKind_BatchFile, InputKind_ConfigFile, MediaError, MediaError_InvalidInput


def _option_kind(name: str) -> InputKind | None:
    if name == "--config-locations":
        return InputKind_ConfigFile()
    if name == "--batch-file" or name == "-a":
        return InputKind_BatchFile()
    return None


def parse_arguments(arguments: CottList[str]) -> Result[CottList[CliInput], MediaError]:
    inputs: list[CliInput] = []
    count: int = len(arguments)
    index: int = 0
    while index < count:
        argument: str = arguments[index]
        index += 1
        if argument.startswith("--") and "=" in argument:
            name, _, inline = argument.partition("=")
            inline_kind: InputKind | None = _option_kind(name)
            if inline_kind is not None:
                if inline == "":
                    return Err(error=MediaError_InvalidInput(message=f"option {name} requires a non-empty value"))
                inputs.append(CliInput(kind=inline_kind, value=inline))
                continue
        kind: InputKind | None = _option_kind(argument)
        if kind is None:
            inputs.append(CliInput(kind=InputKind_Argument(), value=argument))
            continue
        if index >= count:
            return Err(error=MediaError_InvalidInput(message=f"option {argument} requires a value"))
        value: str = arguments[index]
        index += 1
        if value == "":
            return Err(error=MediaError_InvalidInput(message=f"option {argument} requires a non-empty value"))
        inputs.append(CliInput(kind=kind, value=value))
    return Ok(value=CottList(values=inputs))
