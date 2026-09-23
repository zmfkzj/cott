import getpass
import warnings
from typing import Final

import keyring

from cott_runtime import Err, Ok, Result
from real.pgcli_types import ConnectionError, ConnectionError_CredentialUnavailable, ConnectionError_PromptDisabled, CredentialRequest, CredentialResolution, PasswordSource_Environment, PasswordSource_Keyring, PasswordSource_None, PasswordSource_Prompt, PasswordSource_Supplied

_PROMPT: Final[str] = "Password: "
_KEYRING_MISSING_IDENTITY: Final[str] = "keyring lookup requires a service and user"
_KEYRING_FAILED: Final[str] = "keyring credential lookup failed"
_PROMPT_FAILED: Final[str] = "password prompt unavailable or cancelled"


def _unavailable(message: str) -> Result[CredentialResolution, ConnectionError]:
    return Err(error=ConnectionError_CredentialUnavailable(message=message))


def resolve_credential(request: CredentialRequest) -> Result[CredentialResolution, ConnectionError]:
    if request.supplied_password != "":
        return Ok(value=CredentialResolution(password=request.supplied_password, source=PasswordSource_Supplied()))
    if request.environment_password != "":
        return Ok(value=CredentialResolution(password=request.environment_password, source=PasswordSource_Environment()))
    if request.use_keyring:
        if request.service == "" or request.user == "":
            return _unavailable(_KEYRING_MISSING_IDENTITY)
        stored: str | None
        try:
            stored = keyring.get_password(request.service, request.user)
        except Exception:
            return _unavailable(_KEYRING_FAILED)
        if stored is not None and stored != "":
            return Ok(value=CredentialResolution(password=stored, source=PasswordSource_Keyring()))
    if request.no_prompt:
        return Err(error=ConnectionError_PromptDisabled())
    response: str
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            response = getpass.getpass(_PROMPT)
    except (EOFError, KeyboardInterrupt, OSError, getpass.GetPassWarning):
        return _unavailable(_PROMPT_FAILED)
    if response != "":
        return Ok(value=CredentialResolution(password=response, source=PasswordSource_Prompt()))
    return Ok(value=CredentialResolution(password="", source=PasswordSource_None()))
