from cott_runtime import Err, Ok, Result
from curriculum.assignment_rule_types import AccessCodeError, AccessCodeError_EmptyCode, AccessCodeError_TooShort


def validate_access_code(code: str) -> Result[str, AccessCodeError]:
    if len(code) == 0:
        return Err(error=AccessCodeError_EmptyCode())
    if len(code) < 4:
        return Err(error=AccessCodeError_TooShort())
    return Ok(value=code)
