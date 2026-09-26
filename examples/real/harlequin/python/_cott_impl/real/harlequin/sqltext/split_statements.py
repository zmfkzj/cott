from cott_runtime import CottList

from real.harlequin.sqltext import separator_offsets


def split_statements(text: str) -> CottList[str]:
    statements: list[str] = []
    start = 0
    for offset in separator_offsets(text):
        piece = text[start:offset].strip()
        if piece:
            statements.append(piece)
        start = offset
    tail = text[start:].strip()
    if tail:
        statements.append(tail)
    return CottList(values=statements)
