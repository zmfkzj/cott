from cott_runtime import CottList, U64
from wcwidth import wcwidth

from real.harlequin.catalog import visible_entries
from real.harlequin.catalog_types import CatalogEntry, TreeFrame, TreeState
from real.harlequin.style_types import StyledLine, StyledSpan


def _cut(spans: list[StyledSpan], width: int) -> CottList[StyledSpan]:
    result: list[StyledSpan] = []
    used = 0
    for span in spans:
        kept: list[str] = []
        full = False
        for ch in span.text:
            w = max(wcwidth(ch), 0)
            if used + w > width:
                full = True
                break
            used += w
            kept.append(ch)
        if kept:
            result.append(StyledSpan(style=span.style, text="".join(kept)))
        if full:
            break
    return CottList(values=result)


def render_tree(catalog: CottList[CatalogEntry], tree: TreeState, width: U64, height: U64, focused: bool) -> TreeFrame:
    rows = visible_entries(catalog, tree)
    count = len(rows)
    first = tree.first_row
    if count == 0 or width == 0 or height == 0:
        return TreeFrame(lines=CottList(values=[]), first_row=first)
    cursor = min(tree.cursor, count - 1)
    if cursor < first:
        first = cursor
    elif cursor >= first + height:
        first = cursor - height + 1
    expanded = set(tree.expanded)
    lines: list[StyledLine] = []
    for index in range(first, min(first + height, count)):
        entry = rows[index]
        if not entry.expandable:
            marker = "  "
        elif entry.id in expanded:
            marker = "▼ "
        else:
            marker = "▶ "
        label_style = "class:hq.tree.label"
        if focused and index == cursor:
            label_style += " class:hq.cursor"
        spans = [
            StyledSpan(style="class:hq.tree.guide", text="  " * entry.depth + marker),
            StyledSpan(style=label_style, text=entry.label),
        ]
        if entry.type_label != "":
            spans.append(StyledSpan(style="class:hq.tree.type", text=" " + entry.type_label))
        lines.append(StyledLine(spans=_cut(spans, width)))
    return TreeFrame(lines=CottList(values=lines), first_row=first)
