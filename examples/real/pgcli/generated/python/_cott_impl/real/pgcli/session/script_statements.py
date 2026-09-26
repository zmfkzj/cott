import sqlparse
from cott_runtime import CottList


def script_statements(text: str) -> CottList[str]:
    pending: list[str] = [str(piece) for piece in sqlparse.split(text)]
    result: list[str] = []
    while pending:
        piece = pending.pop(0).strip()
        if not piece:
            continue
        if piece.startswith("\\") and "\n" in piece:
            first, rest = piece.split("\n", 1)
            pending = [str(p) for p in sqlparse.split(rest)] + pending
            piece = first.strip()
            if not piece:
                continue
        result.append(piece)
    return CottList(values=result)
