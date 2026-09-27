from cott_runtime import Err, Ok
from frogmouth.document import fetch_remote_document, load_local_document
from frogmouth.document_types import BrowserFailure_DoesNotExist, BrowserFailure_Load, RemoteDocument_Markdown, VisitOutcome, VisitOutcome_Failed, VisitOutcome_Loaded, VisitOutcome_OpenExternally
from frogmouth.locations import inspect_local_path, is_markdown_location, resolve_local_path
from frogmouth.model_types import BrowserContext, Location, LocationKind_Remote, PathKind_Missing


def visit_location(location: Location, context: BrowserContext) -> VisitOutcome:
    is_markdown = is_markdown_location(location, context.markdown_extensions)
    if isinstance(location.kind, LocationKind_Remote):
        if not is_markdown:
            return VisitOutcome_OpenExternally(target=location.target)
        match fetch_remote_document(location.target):
            case Ok(value=RemoteDocument_Markdown(document=document)):
                return VisitOutcome_Loaded(document=document)
            case Ok():
                return VisitOutcome_OpenExternally(target=location.target)
            case Err(error=error):
                return VisitOutcome_Failed(failure=BrowserFailure_Load(cause=error))
    path = resolve_local_path(location.target, context.home, context.working_directory)
    if is_markdown:
        match load_local_document(path):
            case Ok(value=document):
                return VisitOutcome_Loaded(document=document)
            case Err(error=error):
                return VisitOutcome_Failed(failure=BrowserFailure_Load(cause=error))
    if isinstance(inspect_local_path(path), PathKind_Missing):
        return VisitOutcome_Failed(failure=BrowserFailure_DoesNotExist(path=location.target))
    return VisitOutcome_OpenExternally(target="file://" + path)
