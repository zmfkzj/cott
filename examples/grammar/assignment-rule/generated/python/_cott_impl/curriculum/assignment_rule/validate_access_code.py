from cott_runtime import Err, Ok, Result
from curriculum.assignment_rule_types import AccessCodeError, AccessCodeError_TooShort


def validate_access_code(code: str) -> Result[str, AccessCodeError]:
    """Trim an access code and require at least four characters."""
    trimmed: str = code.strip()
    if len(trimmed) < 4:
        return Err(error=AccessCodeError_TooShort())
    return Ok(value=trimmed)
