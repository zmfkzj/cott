import re

import sqlparse
from cott_runtime import CottList


def statement_texts_for_run(text: str) -> CottList[str]:
    text = text.strip()
    if not text:
        return CottList(values=[])
    comments: list[str] = []
    while True:
        match = re.match(r"^(/\*.*?\*/|--.*?)(?:\n|$)", text, re.DOTALL)
        if match is None:
            break
        comments.append(match.group(0))
        text = text[match.end():].lstrip()
    pieces: list[str] = [str(piece) for piece in sqlparse.split(text)]
    if comments and pieces:
        pieces[0] = "".join(comments) + pieces[0]
    elif comments:
        pieces = ["".join(comments)]
    result: list[str] = []
    for piece in pieces:
        formatted = str(sqlparse.format(piece, strip_comments=True)).strip()
        formatted = formatted.rstrip(";").strip()
        if formatted:
            result.append(formatted)
    return CottList(values=result)
