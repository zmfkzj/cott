from __future__ import annotations

from typing import TypeAlias, Union

from curriculum.validated_user_card_types import UserId, UserName, UserCard, CardError, InvalidId
class UserId: ...

class UserName: ...

class UserCard: ...

CardError: TypeAlias = Union[InvalidId]

def run() -> Result[UserCard, CardError]: ...
