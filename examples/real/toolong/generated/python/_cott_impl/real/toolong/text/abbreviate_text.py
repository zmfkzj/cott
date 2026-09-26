from cott_runtime import CottList, U64

from real.toolong.model_types import StyledSpan, StyledText


def abbreviate_text(text: StyledText, limit: U64) -> StyledText:
    if len(text.text) <= limit:
        return text
    spans: list[StyledSpan] = []
    for span in text.spans:
        start = min(span.start, limit)
        end = min(span.end, limit)
        if start < end:
            spans.append(StyledSpan(start=start, end=end, style=span.style))
    return StyledText(text=text.text[:limit] + "\u2026", spans=CottList(values=spans))
