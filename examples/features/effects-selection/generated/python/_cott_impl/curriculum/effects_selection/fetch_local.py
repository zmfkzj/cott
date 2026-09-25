from cott_runtime import CottContractViolation, Err, Ok, Result, _cott_fixture_http
from curriculum.effects_selection_types import EffectError, EffectError_OperationFailed, PageText


def fetch_local(url: str) -> Result[PageText, EffectError]:
    if url == "":
        return Err(error=EffectError_OperationFailed(message="empty url"))
    try:
        body = _cott_fixture_http(url)
        text = body.decode("utf-8", errors="strict")
    except (CottContractViolation, OSError, UnicodeError) as error:
        return Err(error=EffectError_OperationFailed(message=str(error)))
    return Ok(value=PageText(url=url, text=text))
