from __future__ import annotations

from pathlib import Path

from cott_runtime import CottContractViolation, Err, Ok, Result, _cott_fixture_read
from curriculum.effects_selection_types import EffectError, EffectError_InputMissing, EffectError_OperationFailed


def read_text(source: Path) -> Result[str, EffectError]:
    try:
        return Ok(value=_cott_fixture_read(source.as_posix()).decode("utf-8"))
    except CottContractViolation as error:
        if isinstance(error.__cause__, FileNotFoundError):
            return Err(error=EffectError_InputMissing(path=source))
        return Err(error=EffectError_OperationFailed(message=str(error)))
    except UnicodeError as error:
        return Err(error=EffectError_OperationFailed(message=str(error)))
