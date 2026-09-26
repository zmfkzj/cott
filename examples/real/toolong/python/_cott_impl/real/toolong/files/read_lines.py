from cott_runtime import CottList
from real.toolong.files import read_span
from real.toolong.model_types import ByteSpan, LogSource


def read_lines(source: LogSource, spans: CottList[ByteSpan]) -> CottList[str]:
    lines: list[str] = []
    for span in spans:
        raw = read_span(source, span)
        lines.append(raw.decode("utf-8", errors="replace").strip("\n\r").expandtabs(4))
    return CottList(values=lines)
