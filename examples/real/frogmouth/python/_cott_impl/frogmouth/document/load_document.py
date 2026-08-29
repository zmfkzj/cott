from cott_runtime import Err, Ok, Result
from frogmouth.document import (
    derive_document_title,
    load_codeberg_markdown,
    load_github_markdown,
    load_http_markdown,
    load_local_markdown,
    location_title_fallback,
)
from frogmouth.document_types import LoadError
from frogmouth.model_types import (
    Document,
    Location,
    LocationKind_Codeberg,
    LocationKind_GitHub,
    LocationKind_Local,
    LocationKind_Remote,
)


def load_document(location: Location) -> Result[Document, LoadError]:
    match location.kind:
        case LocationKind_Local():
            loaded = load_local_markdown(location.target)
        case LocationKind_Remote():
            loaded = load_http_markdown(location.target)
        case LocationKind_GitHub():
            loaded = load_github_markdown(location.target)
        case LocationKind_Codeberg():
            loaded = load_codeberg_markdown(location.target)

    match loaded:
        case Ok(value=markdown):
            fallback = location_title_fallback(location)
            title = derive_document_title(markdown, fallback)
            return Ok(value=Document(location=location, markdown=markdown, title=title))
        case Err(error=error):
            return Err(error=error)
