from cott_runtime import U64, CottList


def _skip_to(text: str, closer: str, start: int) -> int:
    end = text.find(closer, start)
    return len(text) if end < 0 else end + len(closer)


def _skip_quoted(text: str, quote: str, start: int) -> int:
    i = start
    n = len(text)
    while i < n:
        if text[i] == quote:
            if i + 1 < n and text[i + 1] == quote:
                i += 2
                continue
            return i + 1
        i += 1
    return n


def _dollar_tag_end(text: str, start: int) -> int:
    """Return the index just past a `$tag$` opener at `start`, or -1."""
    n = len(text)
    j = start + 1
    if j < n and (text[j] == "_" or (text[j].isascii() and text[j].isalpha())):
        j += 1
        while j < n and (text[j] == "_" or (text[j].isascii() and text[j].isalnum())):
            j += 1
    if j < n and text[j] == "$":
        return j + 1
    return -1


def separator_offsets(text: str) -> CottList[U64]:
    offsets: list[int] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == ";":
            offsets.append(i + 1)
            i += 1
        elif ch == "'" or ch == '"':
            i = _skip_quoted(text, ch, i + 1)
        elif ch == "`":
            i = _skip_to(text, "`", i + 1)
        elif text.startswith("--", i):
            i = _skip_to(text, "\n", i + 2)
        elif text.startswith("/*", i):
            i = _skip_to(text, "*/", i + 2)
        elif ch == "$":
            tag_end = _dollar_tag_end(text, i)
            if tag_end < 0:
                i += 1
            else:
                i = _skip_to(text, text[i:tag_end], tag_end)
        else:
            i += 1
    return CottList(values=offsets)
