from pathlib import Path

from cott_runtime import CottContractViolation, Err, Ok, Result
from cott_runtime import _cott_fixture_read
from curriculum.effects_selection_types import EffectError, EffectError_InputMissing, EffectError_OperationFailed, FileText


def read_text(source: Path) -> Result[FileText, EffectError]:
    try:
        data = _cott_fixture_read(source)
    except FileNotFoundError:
        return Err(error=EffectError_InputMissing(path=source))
    except CottContractViolation as exc:
        if isinstance(exc.__cause__, FileNotFoundError):
            return Err(error=EffectError_InputMissing(path=source))
        return Err(error=EffectError_OperationFailed(message=str(exc)))
    except OSError as exc:
        return Err(error=EffectError_OperationFailed(message=str(exc)))
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        return Err(error=EffectError_OperationFailed(message=str(exc)))
    return Ok(value=FileText(path=source, text=text))
