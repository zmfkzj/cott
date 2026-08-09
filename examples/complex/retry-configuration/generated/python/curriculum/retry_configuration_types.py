from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class RetryCount:
    value: int

@dataclass(frozen=True, slots=True, kw_only=True)
class RetryConfiguration:
    attempts: RetryCount
    backoff_ms: int

__all__ = ["RetryCount", "RetryConfiguration"]
