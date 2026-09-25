from cott_runtime import CottList, Option, Some
from real.toolong_types import LogEntry


def _ascii_lower(text: str) -> str:
    return "".join(chr(ord(ch) + 32) if "A" <= ch <= "Z" else ch for ch in text)


def filter_entries(entries: CottList[LogEntry], contains: Option[str]) -> CottList[LogEntry]:
    if isinstance(contains, Some):
        needle: str = _ascii_lower(contains.value)
        kept: list[LogEntry] = []
        for entry in entries:
            if needle in _ascii_lower(entry.text):
                kept.append(entry)
        return CottList(values=kept)
    else:
        return entries
