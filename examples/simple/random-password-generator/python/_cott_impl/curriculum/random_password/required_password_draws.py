from cott_runtime import Err, I64, Ok, Result
from curriculum.random_password_types import PasswordError, PasswordError_InvalidLength


def required_password_draws(length: I64) -> Result[I64, PasswordError]:
    if length < 1 or length > 128:
        return Err(error=PasswordError_InvalidLength())
    return Ok(value=2 * length + length // 2 - 1)
