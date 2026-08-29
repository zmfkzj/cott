from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.assignment_rule_types import AccessCodeError as AccessCodeError, AccessCodeError_EmptyCode as AccessCodeError_EmptyCode, AccessCodeError_LegacyFormat as AccessCodeError_LegacyFormat, AccessCodeError_TooShort as AccessCodeError_TooShort, BaseAccessCodeRule as BaseAccessCodeRule, StrictAccessCodeRule as StrictAccessCodeRule
"""Trim an access code and require at least four characters."""
def validate_access_code(code: str) -> Result[str, AccessCodeError]: ...

__all__ = ["AccessCodeError", "AccessCodeError_EmptyCode", "AccessCodeError_LegacyFormat", "AccessCodeError_TooShort", "BaseAccessCodeRule", "StrictAccessCodeRule", "validate_access_code"]
