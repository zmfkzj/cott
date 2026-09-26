from unicodedata import category

from cott_runtime import CottList, Err, Ok, Result
from real.harlequin.cli_types import SshSettings
from real.harlequin.support_types import SshError, SshError_Invalid


def _unsafe_argument(value: str) -> bool:
    return not value or value.startswith("-") or any(
        character.isspace()
        or category(character) == "Cc"
        or character in ";&|`$<>(){}'\"\\"
        for character in value
    )


def _invalid_argument(value: str, role: str) -> Err[SshError]:
    return Err(error=SshError_Invalid(message=f"Refusing to pass {value!r} to ssh: it contains characters ssh would not take as a {role}."))


def ssh_command(settings: SshSettings) -> Result[CottList[str], SshError]:
    if _unsafe_argument(settings.host):
        return _invalid_argument(settings.host, "host")
    command = ["ssh", "-N", "-o", "ExitOnForwardFailure=yes"]
    if settings.batch_mode:
        command.extend(["-o", "BatchMode=yes"])
    for forward in settings.forwards:
        if _unsafe_argument(forward):
            return _invalid_argument(forward, "forward")
        command.extend(["-L", forward])
    command.append(settings.host)
    return Ok(value=CottList(values=command))
