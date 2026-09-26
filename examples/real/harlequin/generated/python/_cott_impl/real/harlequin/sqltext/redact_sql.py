import re
from typing import Final

from cott_runtime import CottList
from real.harlequin.sqltext import redact_text
from real.harlequin.sqltext_types import REDACTED

_URI: Final[str] = "://[^/?#@\\s]*?:([^/?#@\\s]+)@"
_DSN: Final[str] = "[\\w.\\-]*(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)[\\w.\\-]*\\s*=\\s*(?:'([^']*)'|\"([^\"]*)\"|([^&;\\s]+))"
_LITERAL: Final[str] = "[\\w.]*(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|key[_-]?id)[\\w.]*\\s*=?\\s*'([^']*)'"


def _spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for match in re.finditer(_URI, text):
        spans.append(match.span(1))
    for match in re.finditer(_DSN, text, re.IGNORECASE):
        for group in (1, 2, 3):
            if match.group(group) is not None:
                spans.append(match.span(group))
                break
    for match in re.finditer(_LITERAL, text, re.IGNORECASE):
        spans.append(match.span(1))
    return spans


def redact_sql(sql: str, secrets: CottList[str]) -> str:
    text = redact_text(sql, secrets)
    result = text
    floor = len(text) + 1
    for start, end in sorted(set(_spans(text)), reverse=True):
        if end > floor:
            continue
        result = result[:start] + REDACTED + result[end:]
        floor = start
    return result
