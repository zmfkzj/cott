from cott_runtime import CottList
from real.harlequin.sqltext_types import REDACTED


def redact_text(text: str, secrets: CottList[str]) -> str:
    result = text
    for secret in sorted((s for s in secrets if len(s) >= 4), key=len, reverse=True):
        result = result.replace(secret, REDACTED)
    return result
