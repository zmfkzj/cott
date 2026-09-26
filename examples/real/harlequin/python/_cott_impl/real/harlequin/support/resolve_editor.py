import shlex

from cott_runtime import CottList, Err, FrozenMap, Ok, Result
from real.harlequin.support_types import ExternalEditorError, ExternalEditorError_Failed, ExternalEditorError_NoEditor


def resolve_editor(environment: FrozenMap[str, str]) -> Result[CottList[str], ExternalEditorError]:
    for key in ("VISUAL", "EDITOR"):
        if key not in environment:
            continue
        value = environment[key]
        if not value.strip():
            continue
        try:
            command = shlex.split(value, posix=True)
        except ValueError as error:
            return Err(error=ExternalEditorError_Failed(message=f"Harlequin could not run your editor. The editor command {value!r} could not be parsed: {error}"))
        return Ok(value=CottList(values=command))
    return Err(error=ExternalEditorError_NoEditor())
