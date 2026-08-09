from cott_runtime import Ok, Result
from curriculum.validated_user_card_types import CardError, UserCard, UserId, UserName


def run() -> Result[UserCard, CardError]:
    return Ok(value=UserCard(id=UserId(value=7), name=UserName(value="Ada")))
