import re

from real.toolong.model_types import FindQuery
from real.toolong.text_types import LineMatch


def line_matches(line: str, query: FindQuery) -> LineMatch:
    if not line:
        return LineMatch(matched=True, invalid_regex=False)
    if query.regex:
        flags = 0 if query.case_sensitive else re.IGNORECASE
        try:
            found = re.match(query.text, line, flags) is not None
        except re.error:
            return LineMatch(matched=True, invalid_regex=True)
        return LineMatch(matched=found, invalid_regex=False)
    if query.case_sensitive:
        return LineMatch(matched=query.text in line, invalid_regex=False)
    return LineMatch(matched=query.text.lower() in line.lower(), invalid_regex=False)
