from pathlib import Path

from cott_runtime import Err, Ok, Result
from frogmouth.document import load_document
from frogmouth.document_types import OpenError, OpenError_Load, OpenError_Navigation
from frogmouth.model_types import Document
from frogmouth.navigation import resolve_location


def open_location(value: str, working_directory: Path) -> Result[Document, OpenError]:
    resolved = resolve_location(value, working_directory)
    if isinstance(resolved, Err):
        return Err(error=OpenError_Navigation(cause=resolved.error))
    loaded = load_document(resolved.value)
    if isinstance(loaded, Err):
        return Err(error=OpenError_Load(cause=loaded.error))
    return Ok(value=loaded.value)
