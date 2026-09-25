import cott_runtime
from cott_runtime import CottList, Result
from real.yt_dlp_types import CliInput, InputKind_Argument, InputKind_BatchFile, InputKind_ConfigFile, MediaError, MediaError_InvalidInput


def resolve_inputs(inputs: CottList[CliInput], config: CottList[CliInput]) -> Result[CottList[str], MediaError]:
    urls: list[str] = []
    for group in (inputs, config):
        for entry in group:
            if entry.value.strip() == "":
                return cott_runtime.Err(error=MediaError_InvalidInput(message="input URL must not be blank"))
            match entry.kind:
                case InputKind_Argument():
                    urls.append(entry.value)
                case InputKind_ConfigFile() | InputKind_BatchFile():
                    return cott_runtime.Err(error=MediaError_InvalidInput(message="input must be an expanded argument URL"))
    return cott_runtime.Ok(value=CottList(values=urls))
