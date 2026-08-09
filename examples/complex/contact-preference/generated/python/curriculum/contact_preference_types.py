from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias, Union

from cott_runtime import Option, Result, UNIT, Unit
@dataclass(frozen=True, slots=True, kw_only=True)
class Email:
    pass

@dataclass(frozen=True, slots=True, kw_only=True)
class Sms:
    pass

ContactPreference: TypeAlias = Union[Email, Sms]

__all__ = ["ContactPreference", "Email", "Sms"]
