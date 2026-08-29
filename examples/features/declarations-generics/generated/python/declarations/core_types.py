from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
T = TypeVar("T", covariant=True)
N = TypeVar("N", bound=U64)

Label: TypeAlias = str

LABEL_BYTES: Final[U64] = 4

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NonEmptyLabel:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))
        if not ((len(self.value) > 0)):
            raise CottContractViolation("NonEmptyLabel refinement failed", symbol="declarations.core.NonEmptyLabel", phase="refinement", span={"end_byte":124,"end_column":23,"end_line":8,"start_byte":112,"start_column":11,"start_line":8}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LabelFrame(Generic[T]):
    __hash__ = None
    label: NonEmptyLabel
    value: T

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "label", _cott_validate_abi(self.label, NonEmptyLabel, path="$.label"))
        if not _cott_validated_construction():
            object.__setattr__(self, "value", _cott_validate_abi(self.value, T, path="$.value"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ByteBlock(Generic[N]):
    __hash__ = None
    raw: CottBuffer[Literal[N]]

__all__ = ["ByteBlock", "LABEL_BYTES", "Label", "LabelFrame", "NonEmptyLabel"]
