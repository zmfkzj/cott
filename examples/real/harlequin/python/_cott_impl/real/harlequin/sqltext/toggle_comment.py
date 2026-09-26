from real.harlequin.sqltext_types import TextEdit, TextRange


def _indent_width(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _line_of(starts: list[int], lengths: list[int], offset: int) -> int:
    for index in range(len(starts)):
        if offset <= starts[index] + lengths[index]:
            return index
    return len(starts) - 1


def _shift(offset: int, edits: list[tuple[int, int, bool]]) -> int:
    delta = 0
    for pos, size, inserted in edits:
        if inserted:
            if pos <= offset:
                delta += size
        elif offset >= pos + size:
            delta -= size
        elif offset > pos:
            delta -= offset - pos
    return offset + delta


def toggle_comment(text: str, selection: TextRange) -> TextEdit:
    lines = text.split("\n")
    starts: list[int] = []
    lengths: list[int] = []
    position = 0
    for line in lines:
        starts.append(position)
        lengths.append(len(line))
        position += len(line) + 1
    start = int(selection.start)
    end = int(selection.end)
    first = _line_of(starts, lengths, start)
    last = _line_of(starts, lengths, end)
    if start < end and last > first and end == starts[last]:
        last -= 1
    touched = [i for i in range(first, last + 1) if lines[i].strip(" \t") != ""]
    if not touched:
        return TextEdit(text=text, anchor=start, cursor=end)
    uncomment = all(lines[i].lstrip(" \t").startswith("--") for i in touched)
    edits: list[tuple[int, int, bool]] = []
    if uncomment:
        for i in touched:
            width = _indent_width(lines[i])
            size = 3 if lines[i][width:].startswith("-- ") else 2
            edits.append((starts[i] + width, size, False))
            lines[i] = lines[i][:width] + lines[i][width + size :]
    else:
        indent = min(_indent_width(lines[i]) for i in touched)
        for i in touched:
            edits.append((starts[i] + indent, 3, True))
            lines[i] = lines[i][:indent] + "-- " + lines[i][indent:]
    return TextEdit(text="\n".join(lines), anchor=_shift(start, edits), cursor=_shift(end, edits))
