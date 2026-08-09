from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class UserId:
    value: int

@dataclass(frozen=True, slots=True, kw_only=True)
class UserName:
    value: str

@dataclass(frozen=True, slots=True, kw_only=True)
class UserCard:
    id: UserId
    name: UserName

@dataclass(frozen=True, slots=True, kw_only=True)
class InvalidId:
    pass

CardError: TypeAlias = Union[InvalidId]

__all__ = ["UserId", "UserName", "UserCard", "CardError", "InvalidId"]
