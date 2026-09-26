from urllib.parse import urlsplit

from cott_runtime import CottList
from rich.markup import escape

from frogmouth.history_types import History, HistoryEntry
from frogmouth.model_types import Location, LocationKind_Remote


def _split(path: str) -> tuple[str, str]:
    head, sep, name = path.rpartition("/")
    if not sep:
        return name, "."
    if head == "":
        return name, "/"
    return name, head


def _prompt(location: Location) -> str:
    if isinstance(location.kind, LocationKind_Remote):
        parts = urlsplit(location.target)
        name, parent = _split(parts.path)
        host = (parts.hostname or "").lower()
        return f":globe_with_meridians: [bold]{escape(name)}[/]\n[dim]{escape(parent)}\n{escape(host)}[/]"
    name, parent = _split(location.target)
    return f":page_facing_up: [bold]{escape(name)}[/]\n[dim]{escape(parent)}[/]"


def history_entries(history: History) -> CottList[HistoryEntry]:
    locations = list(history.locations)
    return CottList(
        values=[
            HistoryEntry(history_id=index, location=locations[index], prompt=_prompt(locations[index]))
            for index in range(len(locations) - 1, -1, -1)
        ]
    )
