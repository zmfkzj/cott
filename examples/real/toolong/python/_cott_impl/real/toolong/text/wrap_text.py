from rich.console import Console
from rich.text import Span, Text

from cott_runtime import CottList, U16
from real.toolong.model_types import StyledSpan, StyledText


def _to_rich(text: StyledText, styles: list[str]) -> Text:
    spans: list[Span] = []
    for span in text.spans:
        spans.append(Span(span.start, span.end, str(len(styles))))
        styles.append(span.style)
    return Text(text.text, spans=spans)


def _from_rich(line: Text, styles: list[str]) -> StyledText:
    spans: list[StyledSpan] = []
    for span in line.spans:
        spans.append(StyledSpan(start=span.start, end=span.end, style=styles[int(str(span.style))]))
    return StyledText(text=line.plain, spans=CottList(values=spans))


def wrap_text(text: StyledText, width: U16) -> CottList[StyledText]:
    styles: list[str] = []
    rich_text = _to_rich(text, styles)
    lines = rich_text.wrap(Console(), max(width, 1), tab_size=8)
    result: list[StyledText] = []
    for line in lines:
        result.append(_from_rich(line, styles))
    return CottList(values=result)
