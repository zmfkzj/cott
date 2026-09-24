from pathlib import Path

from cott_runtime import Err, Ok, Result
from cott_runtime import _cott_fixture_read
from curriculum.effects_selection_types import EffectError, EffectError_InputMissing, EffectError_OperationFailed


def read_text(source: Path) -> Result[str, EffectError]:
    try:
        data = _cott_fixture_read(source)
    except FileNotFoundError:
        return Err(error=EffectError_InputMissing(path=source))
    except Exception as exc:
        return Err(error=EffectError_OperationFailed(message=str(exc)))
    if isinstance(data, str):
        return Ok(value=data)
    try:
        return Ok(value=bytes(data).decode("utf-8"))
    except UnicodeDecodeError as exc:
        return Err(error=EffectError_OperationFailed(message=str(exc)))
