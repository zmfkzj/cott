import re

from real.harlequin.sqltext_types import REDACTED


def _secret_spans(connection: str) -> list[tuple[int, int]]:
    uri_pattern = "://[^/?#@\\s]*?:([^/?#@\\s]+)@"
    dsn_pattern = (
        "[\\w.\\-]*(?:password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key)[\\w.\\-]*"
        "\\s*=\\s*(?:'([^']*)'|\"([^\"]*)\"|([^&;\\s]+))"
    )
    spans: list[tuple[int, int]] = []
    for match in re.finditer(uri_pattern, connection):
        spans.append((match.start(1), match.end(1)))
    for match in re.finditer(dsn_pattern, connection, re.IGNORECASE):
        for group in (1, 2, 3):
            if match.group(group) is not None:
                spans.append((match.start(group), match.end(group)))
                break
    return spans


def redact_connection_string(connection: str) -> str:
    spans = sorted(_secret_spans(connection), reverse=True)
    result = connection
    replaced: list[tuple[int, int]] = []
    for start, end in spans:
        if any(start < r_end and r_start < end for r_start, r_end in replaced):
            continue
        result = result[:start] + REDACTED + result[end:]
        replaced.append((start, end))
    return result
