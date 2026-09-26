from cott_runtime import CottContractViolation, Err, Ok, Result, _cott_fixture_read
from frogmouth.document_types import LoadError, LoadError_LocalFailed
from frogmouth.model_types import Document, Location, LocationKind_Local


def _read_bytes(path: str) -> bytes:
    try:
        return _cott_fixture_read(path)
    except CottContractViolation as violation:
        if violation.message != "fixture adapters are inactive":
            cause = violation.__cause__
            if isinstance(cause, OSError):
                raise cause from None
            raise
    with open(path, "rb") as handle:
        return handle.read()


def load_local_document(path: str) -> Result[Document, LoadError]:
    try:
        data = _read_bytes(path)
    except OSError as error:
        return Err(error=LoadError_LocalFailed(path=path, message=str(error)))
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        return Err(error=LoadError_LocalFailed(path=path, message=str(error)))
    markdown = text.replace("\r\n", "\n").replace("\r", "\n")
    return Ok(value=Document(location=Location(kind=LocationKind_Local(), target=path), markdown=markdown))
