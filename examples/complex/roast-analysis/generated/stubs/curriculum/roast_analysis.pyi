from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.roast_analysis_types import RoastAnalysis as RoastAnalysis, RoastAnalysisError as RoastAnalysisError, RoastAnalysisError_EmptySamples as RoastAnalysisError_EmptySamples, RoastAnalysisError_NonIncreasingTime as RoastAnalysisError_NonIncreasingTime, RoastProfile as RoastProfile, TemperatureSample as TemperatureSample
"""Validate that a roast profile has at least one sample and strictly
increasing elapsed times. EmptySamples takes priority over the first
NonIncreasingTime violation."""
def validate_roast_profile(profile: RoastProfile) -> Result[Unit, RoastAnalysisError]: ...

"""Summarize a nonempty sample sequence. The peak is the earliest sample at
the maximum temperature, and total rise is the final temperature minus the
first temperature."""
def summarize_roast_samples(samples: CottList[TemperatureSample]) -> RoastAnalysis: ...

"""Validate a roast profile, then summarize its samples without repeating
chronology checks."""
def analyze_roast_profile(profile: RoastProfile) -> Result[RoastAnalysis, RoastAnalysisError]: ...

__all__ = ["RoastAnalysis", "RoastAnalysisError", "RoastAnalysisError_EmptySamples", "RoastAnalysisError_NonIncreasingTime", "RoastProfile", "TemperatureSample", "analyze_roast_profile", "summarize_roast_samples", "validate_roast_profile"]
