from __future__ import annotations

from typing import TypeAlias, Union

from curriculum.access_grant_types import PrincipalId, AccessGrant, Granted, Denied, AccessError, MissingRole
class PrincipalId: ...

AccessGrant: TypeAlias = Union[Granted, Denied]

AccessError: TypeAlias = Union[MissingRole]

def run() -> Result[AccessGrant, AccessError]: ...
