from frogmouth.model_types import Location


def _heading_text(line: str) -> str | None:
    run = len(line) - len(line.lstrip("#"))
    if run < 1 or run > 6 or line[run:run + 1] != " ":
        return None
    return line[run:].strip(" \t")


def derive_title(location: Location, markdown: str) -> str:
    for raw in markdown.split("\n"):
        line = raw[:-1] if raw.endswith("\r") else raw
        text = _heading_text(line)
        if text:
            return text
    target = location.target
    for segment in reversed(target.split("/")):
        if segment:
            return segment
    return target
