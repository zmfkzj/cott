import re
from typing import Final

from cott_runtime import CottList
from real.toolong.model_types import FindQuery, StyledSpan, StyledText

_MATCH_STYLE: Final[str] = "fg:#000000 bg:#fea62b"
_DIM_STYLE: Final[str] = "dim"


def highlight_find(text: StyledText, query: FindQuery) -> StyledText:
    if query.text == "":
        return text
    flags = 0 if query.case_sensitive else re.IGNORECASE
    source = query.text if query.regex else re.escape(query.text)
    try:
        matches = list(re.finditer(source, text.text, flags))
    except re.error:
        return text
    spans = [span for span in text.spans]
    matched = False
    for match in matches:
        start, end = match.span()
        if start == end:
            continue
        matched = True
        spans.append(StyledSpan(start=start, end=end, style=_MATCH_STYLE))
    if not matched and text.text != "":
        spans.append(StyledSpan(start=0, end=len(text.text), style=_DIM_STYLE))
    return StyledText(text=text.text, spans=CottList(values=spans))
