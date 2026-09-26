import json

from cott_runtime import CottList, Nothing, Option, Some
from rich.json import JSON

from real.toolong.text import highlight_json
from real.toolong.model_types import StyledSpan, StyledText


def pretty_json(line: str) -> Option[StyledText]:
    try:
        value: object = json.loads(line)
    except ValueError:
        return Nothing()
    plain: str = JSON.from_data(value).text.plain
    spans: list[StyledSpan] = []
    return Some(value=highlight_json(StyledText(text=plain, spans=CottList(values=spans))))
