from cott_runtime import Ok
from curriculum.validated_user_card_types import UserCard, UserId, UserName


def run() -> Ok[UserCard]:
    return Ok(value=UserCard(id=UserId(value=7), name=UserName(value="Ada")))
