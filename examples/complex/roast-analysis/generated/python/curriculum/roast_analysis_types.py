from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TemperatureSample:
    __hash__ = None
    elapsed_s: U32
    bean_temp_deci_c: I32

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RoastProfile:
    __hash__ = None
    samples: CottList[TemperatureSample]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RoastAnalysis:
    __hash__ = None
    peak_temp_deci_c: I32
    peak_at_s: U32
    total_rise_deci_c: I64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RoastAnalysisError_EmptySamples:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RoastAnalysisError_NonIncreasingTime:
    pass

RoastAnalysisError: TypeAlias = Union[RoastAnalysisError_EmptySamples, RoastAnalysisError_NonIncreasingTime]

"""Validate that a roast profile has at least one sample and strictly
increasing elapsed times. EmptySamples takes priority over the first
NonIncreasingTime violation."""
"""Summarize a nonempty sample sequence. The peak is the earliest sample at
the maximum temperature, and total rise is the final temperature minus the
first temperature."""
"""Validate a roast profile, then summarize its samples without repeating
chronology checks."""
__all__ = ["RoastAnalysis", "RoastAnalysisError", "RoastAnalysisError_EmptySamples", "RoastAnalysisError_NonIncreasingTime", "RoastProfile", "TemperatureSample"]
