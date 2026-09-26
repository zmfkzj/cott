from cott_runtime import CottList

from real.harlequin.sqltext import separator_offsets
from real.harlequin.sqltext_types import TextRange


def selected_queries(text: str, selection: TextRange) -> CottList[str]:
    if not text.strip():
        return CottList(values=[])
    if ";" not in text:
        return CottList(values=[text])
    offsets: list[int] = [int(offset) for offset in separator_offsets(text)]
    if not offsets:
        return CottList(values=[text])
    boundaries: list[int] = [0, *offsets, len(text)]
    kept: list[tuple[str, int, int]] = []
    for index in range(len(boundaries) - 1):
        query_start = boundaries[index]
        query_end = boundaries[index + 1]
        query = text[query_start:query_end].strip()
        if query:
            kept.append((query, query_start, query_end))
    if not kept:
        return CottList(values=[])
    sel_start = min(int(selection.start), int(selection.end))
    sel_end = max(int(selection.start), int(selection.end))
    overlapping: list[str] = [q for q, qs, qe in kept if qs < sel_end and qe > sel_start]
    if overlapping:
        return CottList(values=overlapping)
    for q, _qs, qe in kept:
        if qe >= sel_start:
            return CottList(values=[q])
    return CottList(values=[kept[-1][0]])
