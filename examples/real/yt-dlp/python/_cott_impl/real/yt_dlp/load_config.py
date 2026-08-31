from pathlib import Path

from cott_runtime import CottList, Err, Ok, Result, _cott_fixture_read
from real.yt_dlp import parse_arguments
from real.yt_dlp_types import CliInput, MediaError, MediaError_InvalidConfig, MediaError_InvalidInput


def _tokenize_config(content: str) -> tuple[CottList[str], str]:
    arguments: list[str] = []
    token: list[str] = []
    token_started: bool = False
    quote: str = ""
    index: int = 0
    while index < len(content):
        character: str = content[index]
        if quote == "'":
            if character == "'":
                quote = ""
            else:
                token.append(character)
            index += 1
            continue
        if quote == '"':
            if character == '"':
                quote = ""
                index += 1
                continue
            if character == "\\":
                index += 1
                if index == len(content):
                    return CottList(values=tuple(arguments)), "trailing escape in configuration"
                if content[index] == "\n":
                    index += 1
                    continue
                if content[index] != '"' and content[index] != "\\":
                    token.append("\\")
                token.append(content[index])
                index += 1
                continue
            token.append(character)
            index += 1
            continue
        if character == "#":
            if token_started:
                if len(arguments) == 100000:
                    return CottList(values=tuple(arguments)), "configuration contains more than 100000 arguments"
                arguments.append("".join(token))
                token = []
                token_started = False
            while index < len(content) and content[index] != "\n":
                index += 1
            continue
        if character.isspace():
            if token_started:
                if len(arguments) == 100000:
                    return CottList(values=tuple(arguments)), "configuration contains more than 100000 arguments"
                arguments.append("".join(token))
                token = []
                token_started = False
            index += 1
            continue
        if character == "'" or character == '"':
            quote = character
            token_started = True
            index += 1
            continue
        if character == "\\":
            token_started = True
            index += 1
            if index == len(content):
                return CottList(values=tuple(arguments)), "trailing escape in configuration"
            if content[index] != "\n":
                token.append(content[index])
            index += 1
            continue
        token_started = True
        token.append(character)
        index += 1
    if quote != "":
        return CottList(values=tuple(arguments)), "unterminated quote in configuration"
    if token_started:
        if len(arguments) == 100000:
            return CottList(values=tuple(arguments)), "configuration contains more than 100000 arguments"
        arguments.append("".join(token))
    return CottList(values=tuple(arguments)), ""


def load_config(path: Path) -> Result[CottList[CliInput], MediaError]:
    content: str = _cott_fixture_read(path).decode("utf-8-sig")
    arguments: CottList[str]
    message: str
    arguments, message = _tokenize_config(content)
    if message != "":
        return Err(error=MediaError_InvalidConfig(path=path, message=message))
    match parse_arguments(arguments):
        case Ok(value=inputs):
            if len(inputs) > 100000:
                return Err(
                    error=MediaError_InvalidConfig(
                        path=path,
                        message="configuration contains more than 100000 inputs",
                    )
                )
            return Ok(value=inputs)
        case Err(error=MediaError_InvalidInput(message=message)):
            return Err(error=MediaError_InvalidConfig(path=path, message=message))
        case Err():
            return Err(error=MediaError_InvalidConfig(path=path, message="invalid configuration"))
