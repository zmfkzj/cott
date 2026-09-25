from pathlib import Path

from cott_runtime import CottContractViolation, Err, Ok, Result, _cott_fixture_replace
from curriculum.effects_selection import read_text
from curriculum.effects_selection_types import CopyReceipt, EffectError, EffectError_OperationFailed


def copy_text(source: Path, destination: Path) -> Result[CopyReceipt, EffectError]:
    match read_text(source):
        case Err(error=error):
            return Err(error=error)
        case Ok(value=file):
            data = file.text.encode("utf-8")
            try:
                _cott_fixture_replace(destination, data)
            except (OSError, CottContractViolation) as exc:
                return Err(error=EffectError_OperationFailed(message=str(exc)))
            return Ok(value=CopyReceipt(destination=destination, bytes_written=len(data)))
