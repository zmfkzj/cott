from __future__ import annotations

from pathlib import Path

from cott_runtime import CottContractViolation, Err, Ok, Result, U64, _cott_fixture_replace
from curriculum.effects_selection import read_text
from curriculum.effects_selection_types import EffectError, EffectError_OperationFailed


def copy_text(source: Path, destination: Path) -> Result[U64, EffectError]:
    source_text = read_text(source)
    if isinstance(source_text, Err):
        return Err(error=source_text.error)
    try:
        data = source_text.value.encode("utf-8")
        _cott_fixture_replace(destination.as_posix(), data)
        return Ok(value=len(data))
    except (CottContractViolation, UnicodeError) as error:
        return Err(error=EffectError_OperationFailed(message=str(error)))
