import re

from real.pgcli.parseutils_types import WordBoundary, WordBoundary_AlphanumUnderscore, WordBoundary_ManyPunctuations, WordBoundary_MostPunctuations


def last_word(text: str, boundary: WordBoundary) -> str:
    if not text or text[-1].isspace():
        return ""
    if isinstance(boundary, WordBoundary_AlphanumUnderscore):
        pattern = r"(\w+)$"
    elif isinstance(boundary, WordBoundary_ManyPunctuations):
        pattern = r"([^():,\s]+)$"
    elif isinstance(boundary, WordBoundary_MostPunctuations):
        pattern = r"([^\.():,\s]+)$"
    else:
        pattern = r"([^\s]+)$"
    match = re.search(pattern, text)
    if match is None:
        return ""
    return match.group(0)
