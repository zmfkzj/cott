from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AcceptedLabel:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))
        if not ((len(self.value) > 0)):
            raise CottContractViolation("AcceptedLabel refinement failed", symbol="curriculum.contracts_evidence.AcceptedLabel", phase="refinement", span={"end_byte":87,"end_column":23,"end_line":4,"start_byte":75,"start_column":11,"start_line":4}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LabelRequest:
    __hash__ = None
    label: Option[str]
    minimum_length: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "label", _cott_validate_abi(self.label, Option[str], path="$.label"))
        if not _cott_validated_construction():
            object.__setattr__(self, "minimum_length", _cott_validate_abi(self.minimum_length, U64, path="$.minimum_length"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LabelAssessment:
    __hash__ = None
    text: str
    length: U64
    label: AcceptedLabel

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "length", _cott_validate_abi(self.length, U64, path="$.length"))
        if not _cott_validated_construction():
            object.__setattr__(self, "label", _cott_validate_abi(self.label, AcceptedLabel, path="$.label"))
        if not ((len((self).text) == (self).length)):
            raise CottContractViolation("invariant failed", symbol="curriculum.contracts_evidence.LabelAssessment", clause="invariant:0", phase="invariant", span={"end_byte":280,"end_column":43,"end_line":15,"start_byte":242,"start_column":5,"start_line":15}, expected="true", actual="false")
        if not (((self).text == ((self).label).value)):
            raise CottContractViolation("invariant failed", symbol="curriculum.contracts_evidence.LabelAssessment", clause="invariant:1", phase="invariant", span={"end_byte":324,"end_column":44,"end_line":16,"start_byte":285,"start_column":5,"start_line":16}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LabelEvidenceError_Legacy:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LabelEvidenceError_Missing:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LabelEvidenceError_TooShort:
    __hash__ = None
    actual: str

LabelEvidenceError: TypeAlias = Union[LabelEvidenceError_Legacy, LabelEvidenceError_Missing, LabelEvidenceError_TooShort]

class BaselineLabelRule:
    pass

class RefinedLabelRule(BaselineLabelRule):
    pass

"""Assess labels directly: missing labels and labels shorter than the requested
minimum are declared errors; successful labels are nominally refined and
meet the request's minimum length."""
__all__ = ["AcceptedLabel", "BaselineLabelRule", "LabelAssessment", "LabelEvidenceError", "LabelEvidenceError_Legacy", "LabelEvidenceError_Missing", "LabelEvidenceError_TooShort", "LabelRequest", "RefinedLabelRule"]
