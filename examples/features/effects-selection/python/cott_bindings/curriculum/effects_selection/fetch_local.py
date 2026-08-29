from __future__ import annotations

from cott_runtime import CottContractViolation, Err, Ok, Result, _cott_fixture_http
from curriculum.effects_selection_types import EffectError, EffectError_OperationFailed


def fetch_local(url: str) -> Result[str, EffectError]:
    try:
        return Ok(value=_cott_fixture_http(url).decode("utf-8"))
    except (CottContractViolation, UnicodeError) as error:
        return Err(error=EffectError_OperationFailed(message=str(error)))
