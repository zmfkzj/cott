from pathlib import Path

from cott_runtime import U64, Err, Ok, Result, _cott_fixture_replace
from curriculum.effects_selection import read_text
from curriculum.effects_selection_types import EffectError, EffectError_OperationFailed


def copy_text(source: Path, destination: Path) -> Result[U64, EffectError]:
    match read_text(source):
        case Err(error=error):
            return Err(error=error)
        case Ok(value=text):
            data = text.encode("utf-8")
            try:
                _cott_fixture_replace(destination, data)
            except Exception as exc:
                return Err(error=EffectError_OperationFailed(message=str(exc)))
            return Ok(value=len(data))
