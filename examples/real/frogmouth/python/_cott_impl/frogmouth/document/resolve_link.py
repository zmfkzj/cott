from urllib.parse import urljoin

from cott_runtime import Nothing, Option, Some
from frogmouth.document_types import BrowserFailure_UnhandledLink, LinkAction, LinkAction_Anchor, LinkAction_Failed, LinkAction_OpenExternally, LinkAction_Visit
from frogmouth.locations import inspect_local_path, normalize_local_path, remote_location
from frogmouth.model_types import BrowserContext, Location, LocationKind_Local, LocationKind_Remote, PathKind_Missing


def _local_visit(path: str, anchor: Option[str]) -> LinkAction:
    return LinkAction_Visit(location=Location(kind=LocationKind_Local(), target=path), anchor=anchor)


def _parent_directory(path: str) -> str:
    index = path.rfind("/")
    if index < 0:
        return "."
    if index == 0:
        return "/"
    return path[:index]


def resolve_link(href: str, current: Option[Location], context: BrowserContext) -> LinkAction:
    if href.startswith("#"):
        return LinkAction_Anchor(anchor=href[1:])
    base, has_hash, fragment = href.partition("#")
    anchor: Option[str] = Some(value=fragment) if has_hash and fragment else Nothing()

    remote = remote_location(base)
    if isinstance(remote, Some):
        return LinkAction_Visit(location=remote.value, anchor=anchor)

    viewed: Location | None = current.value if isinstance(current, Some) else None

    if viewed is not None and isinstance(viewed.kind, LocationKind_Remote):
        joined = urljoin(viewed.target, base)
        joined_remote = remote_location(joined)
        if isinstance(joined_remote, Some):
            return LinkAction_Visit(location=joined_remote.value, anchor=anchor)
        return LinkAction_OpenExternally(target=joined)

    direct = normalize_local_path(context.working_directory, base)
    if not isinstance(inspect_local_path(direct), PathKind_Missing):
        return _local_visit(direct, anchor)

    if viewed is not None and isinstance(viewed.kind, LocationKind_Local):
        directory = _parent_directory(normalize_local_path(context.working_directory, viewed.target))
        relative = normalize_local_path(directory, base)
        if not isinstance(inspect_local_path(relative), PathKind_Missing):
            return _local_visit(relative, anchor)

    return LinkAction_Failed(failure=BrowserFailure_UnhandledLink(href=href))
