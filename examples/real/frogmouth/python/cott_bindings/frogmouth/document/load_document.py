from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from cott_runtime import Err, Ok, Result
from frogmouth.document_types import (
    LoadError,
    LoadError_InvalidEncoding,
    LoadError_NetworkFailed,
    LoadError_NotFound,
    LoadError_ReadFailed,
    LoadError_TooLarge,
)
from frogmouth.model_types import Document, Location, LocationKind_Local



def _title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            if title:
                return title
    return fallback or "Frogmouth"


def load_document(location: Location) -> Result[Document, LoadError]:
    source = location.target
    if isinstance(location.kind, LocationKind_Local):
        path = Path(source)
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            return Err(error=LoadError_NotFound(source=source))
        except OSError as error:
            return Err(error=LoadError_ReadFailed(source=source, message=str(error)))
        fallback = path.stem
    else:
        try:
            with urlopen(source, timeout=30) as response:
                data = response.read(5_242_881)
                fallback = response.url.rsplit("/", 1)[-1]
        except HTTPError as error:
            if error.code == 404:
                return Err(error=LoadError_NotFound(source=source))
            return Err(error=LoadError_NetworkFailed(source=source, message=str(error)))
        except (URLError, TimeoutError, ValueError) as error:
            return Err(error=LoadError_NetworkFailed(source=source, message=str(error)))
    if len(data) > 5_242_880:
        return Err(error=LoadError_TooLarge(source=source))
    try:
        markdown = data.decode("utf-8")
    except UnicodeDecodeError:
        return Err(error=LoadError_InvalidEncoding(source=source))
    return Ok(value=Document(location=location, title=_title(markdown, fallback), markdown=markdown))
