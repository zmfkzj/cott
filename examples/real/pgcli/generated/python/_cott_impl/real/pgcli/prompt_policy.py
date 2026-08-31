from cott_runtime import Err, Ok, Result
from real.pgcli_types import (
    ConnectionError,
    ConnectionError_PromptDisabled,
    PromptAction,
    PromptAction_PromptPassword,
    PromptAction_UsePassword,
)


def prompt_policy(no_prompt: bool, password: str) -> Result[PromptAction, ConnectionError]:
    if password != "":
        return Ok(value=PromptAction_UsePassword())
    if no_prompt:
        return Err(error=ConnectionError_PromptDisabled())
    return Ok(value=PromptAction_PromptPassword())
