from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
MAX_PAYLOAD_SIZE: Final[U32] = 8192

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Probability:
    value: F32

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, F32, path="$.value"))
        if not ((0 <= self.value <= 1)):
            raise CottContractViolation("Probability refinement failed", symbol="foo.bar.Probability", phase="refinement", span={"end_byte":105,"end_column":29,"end_line":6,"start_byte":87,"start_column":11,"start_line":6}, expected="true", actual="false")

    __hash__ = None
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PayloadSize:
    value: U32

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, U32, path="$.value"))
        if not ((1 <= self.value <= MAX_PAYLOAD_SIZE)):
            raise CottContractViolation("PayloadSize refinement failed", symbol="foo.bar.PayloadSize", phase="refinement", span={"end_byte":171,"end_column":40,"end_line":9,"start_byte":142,"start_column":11,"start_line":9}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PayloadFormat_Raw:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PayloadFormat_Text:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PayloadFormat_Structured:
    pass

PayloadFormat: TypeAlias = Union[PayloadFormat_Raw, PayloadFormat_Text, PayloadFormat_Structured]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class InputPayload:
    __hash__ = None
    data: bytes
    declared_size: PayloadSize
    format: PayloadFormat

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OutputPayload:
    __hash__ = None
    data: bytes
    source_size: PayloadSize
    format: PayloadFormat

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BarError_InvalidPayload:
    __hash__ = None
    reason: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BarError_ServiceUnavailable:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BarError_ProcessingFailed:
    __hash__ = None
    message: str

BarError: TypeAlias = Union[BarError_InvalidPayload, BarError_ServiceUnavailable, BarError_ProcessingFailed]

_cott_default_BarOptions_threshold: Final[Probability] = Probability(value=0.5)
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BarOptions:
    __hash__ = None
    threshold: Probability = _dataclasses.field(default_factory=lambda: _cott_default_BarOptions_threshold)
    use_cache: bool = False

"""Reject empty payload bytes before any effectful processing."""
"""Perform the effectful byte-processing step without changing payload bytes."""
"""Construct output from processed bytes and the original payload metadata."""
"""Validate, process, and construct output through the three direct helpers."""
__all__ = ["BarError", "BarError_InvalidPayload", "BarError_ProcessingFailed", "BarError_ServiceUnavailable", "BarOptions", "InputPayload", "MAX_PAYLOAD_SIZE", "OutputPayload", "PayloadFormat", "PayloadFormat_Raw", "PayloadFormat_Structured", "PayloadFormat_Text", "PayloadSize", "Probability"]
