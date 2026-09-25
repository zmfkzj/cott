from collections.abc import Iterator

from curriculum.boundary_protocols_types import TextBuffer


def _lines(buffer: TextBuffer) -> Iterator[str]:
    pending: list[str] = []
    after_cr = False
    while True:
        chunk = buffer.readline()
        if not chunk:
            break
        start = 0
        if after_cr and chunk[0] == "\n":
            start = 1
        after_cr = False
        i = start
        n = len(chunk)
        while i < n:
            ch = chunk[i]
            if ch == "\n" or ch == "\r":
                pending.append(chunk[start:i])
                yield "".join(pending)
                pending = []
                if ch == "\r":
                    if i + 1 < n:
                        if chunk[i + 1] == "\n":
                            i += 1
                    else:
                        after_cr = True
                start = i + 1
            i += 1
        if start < n:
            pending.append(chunk[start:])
    if pending:
        yield "".join(pending)


def iter_lines(buffer: TextBuffer) -> Iterator[str]:
    return _lines(buffer)
