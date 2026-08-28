from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
"""Spell one integer from zero through nine hundred ninety-nine.

Hundreds use `and` before a nonzero remainder. Words are lowercase and
separated by one ASCII space, without commas or hyphens."""
"""Render an I64 as a canonical English cardinal.

Zero is `Zero`. Negative values begin with `(negative) `. The first number
word is capitalized and all later words are lowercase. Words use one ASCII
space with no commas or hyphens.

The magnitude is visited in descending three-digit groups. Zero groups are
omitted; each nonzero group is spelled by spell_under_thousand and paired
with `thousand`, `million`, `billion`, `trillion`, `quadrillion`, or
`quintillion`, the greatest scale needed by I64. A final group below one
hundred follows a higher group with `and`. All I64 values, including the
minimum, are accepted without signed-I64 negation."""
__all__ = []
