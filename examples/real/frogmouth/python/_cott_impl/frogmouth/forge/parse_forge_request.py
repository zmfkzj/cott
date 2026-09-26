import re
from typing import Final

from cott_runtime import Nothing, Option, Some
from frogmouth.model_types import ForgeRequest

_PLAIN: Final[str] = "^(?P<owner>[^/ ]+)[/ ](?P<repo>[^ :]+)(?: +(?P<file>[^ ]+))?$"
_BRANCHED: Final[str] = "^(?P<owner>[^/ ]+)[/ ](?P<repo>[^ :]+):(?P<branch>[^ ]+)(?: +(?P<file>[^ ]+))?$"


def _optional(value: str | None) -> Option[str]:
    return Nothing() if value is None else Some(value=value)


def parse_forge_request(arguments: str) -> Option[ForgeRequest]:
    text = arguments.strip()
    plain = re.match(_PLAIN, text)
    if plain is not None:
        return Some(value=ForgeRequest(owner=plain.group("owner"), repository=plain.group("repo"), branch=Nothing(), file=_optional(plain.group("file"))))
    branched = re.match(_BRANCHED, text)
    if branched is not None:
        return Some(value=ForgeRequest(owner=branched.group("owner"), repository=branched.group("repo"), branch=_optional(branched.group("branch")), file=_optional(branched.group("file"))))
    return Nothing()
