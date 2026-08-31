from cott_runtime import Err, Ok, Result
from real.pgcli_types import (
    ConnectionError,
    ConnectionError_CredentialUnavailable,
    ConnectionError_PromptDisabled,
    CredentialRequest,
    CredentialResolution,
    PasswordSource_Environment,
    PasswordSource_Supplied,
)


def resolve_credential(request: CredentialRequest) -> Result[CredentialResolution, ConnectionError]:
    if request.supplied_password != "":
        return Ok(
            value=CredentialResolution(
                password=request.supplied_password,
                source=PasswordSource_Supplied(),
            )
        )
    if request.environment_password != "":
        return Ok(
            value=CredentialResolution(
                password=request.environment_password,
                source=PasswordSource_Environment(),
            )
        )
    if request.use_keyring:
        return Err(
            error=ConnectionError_CredentialUnavailable(
                message="keyring lookup requires an unavailable file.read or network host binding",
            )
        )
    if request.no_prompt:
        return Err(error=ConnectionError_PromptDisabled())
    return Err(
        error=ConnectionError_CredentialUnavailable(
            message="password prompting requires an unavailable network host binding",
        )
    )
