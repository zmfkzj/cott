from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class PrincipalId:
    value: int

@dataclass(frozen=True, slots=True, kw_only=True)
class Granted:
    pass

@dataclass(frozen=True, slots=True, kw_only=True)
class Denied:
    reason: str

AccessGrant: TypeAlias = Union[Granted, Denied]

@dataclass(frozen=True, slots=True, kw_only=True)
class MissingRole:
    pass

AccessError: TypeAlias = Union[MissingRole]

__all__ = ["PrincipalId", "AccessGrant", "Granted", "Denied", "AccessError", "MissingRole"]
