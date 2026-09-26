from cott_runtime import CottList
from frogmouth.locations import inspect_local_path, is_markdown_location
from frogmouth.model_types import Location, LocationKind_Local, PathKind_Directory, PathKind_File


def select_browsable_entries(paths: CottList[str], extensions: CottList[str]) -> CottList[str]:
    kept: list[str] = []
    for path in paths:
        kind = inspect_local_path(path)
        if isinstance(kind, PathKind_Directory):
            if not path.rsplit("/", 1)[-1].startswith("."):
                kept.append(path)
        elif isinstance(kind, PathKind_File):
            if is_markdown_location(Location(kind=LocationKind_Local(), target=path), extensions):
                kept.append(path)
    return CottList(values=kept)
