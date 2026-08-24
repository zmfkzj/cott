from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.roast_analysis_types import RoastAnalysis, RoastAnalysisError, RoastAnalysisError_EmptySamples, RoastAnalysisError_NonIncreasingTime, RoastProfile, TemperatureSample

def validate_roast_profile(profile: RoastProfile) -> Result[Unit, RoastAnalysisError]:
    """Validate that a roast profile has at least one sample and strictly
increasing elapsed times. EmptySamples takes priority over the first
NonIncreasingTime violation."""
    profile = _cott_validate_abi(profile, RoastProfile, path="$.profile")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((profile).samples) == 0)):
        _expected_error = RoastAnalysisError_EmptySamples
        _expected_error_span = {"end_byte":680,"end_column":72,"end_line":26,"start_byte":613,"start_column":5,"start_line":26}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/roast_analysis/validate_roast_profile.py", "cec91239dd9708d0aa3e0b95ee9d43541169248d6271ad221f7a125c4227cbfb", "validate_roast_profile", expected_project_name="roast-analysis", expected_cott_symbol="curriculum.roast_analysis.validate_roast_profile")
        _result = _implementation(profile)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.roast_analysis.validate_roast_profile"
        if _error.span is None:
            _error.span = {"end_byte":745,"end_column":1,"end_line":31,"start_byte":325,"start_column":1,"start_line":19}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.roast_analysis.validate_roast_profile", phase="implementation-call", span={"end_byte":745,"end_column":1,"end_line":31,"start_byte":325,"start_column":1,"start_line":19}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.roast_analysis.validate_roast_profile", phase="implementation-call", span={"end_byte":745,"end_column":1,"end_line":31,"start_byte":325,"start_column":1,"start_line":19}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, RoastAnalysisError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.roast_analysis.validate_roast_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (RoastAnalysisError_NonIncreasingTime,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.roast_analysis.validate_roast_profile", phase="error", span={"end_byte":745,"end_column":1,"end_line":31,"start_byte":325,"start_column":1,"start_line":19}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.roast_analysis.validate_roast_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    return _result

def summarize_roast_samples(samples: CottList[TemperatureSample]) -> RoastAnalysis:
    """Summarize a nonempty sample sequence. The peak is the earliest sample at
the maximum temperature, and total rise is the final temperature minus the
first temperature."""
    samples = _cott_validate_abi(samples, CottList[TemperatureSample], path="$.samples")
    if not ((len(samples) > 0)):
        raise CottContractViolation("requires clause failed", symbol="curriculum.roast_analysis.summarize_roast_samples", clause="requires:1", phase="requires", span={"end_byte":1052,"end_column":29,"end_line":38,"start_byte":1028,"start_column":5,"start_line":38}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/roast_analysis/summarize_roast_samples.py", "bd760f964f9a2fe7e183ae92046f8a0eee75e88a7073ecfd99d6f6331645bdd0", "summarize_roast_samples", expected_project_name="roast-analysis", expected_cott_symbol="curriculum.roast_analysis.summarize_roast_samples")
        _result = _implementation(samples)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.roast_analysis.summarize_roast_samples"
        if _error.span is None:
            _error.span = {"end_byte":1070,"end_column":1,"end_line":42,"start_byte":745,"start_column":1,"start_line":31}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.roast_analysis.summarize_roast_samples", phase="implementation-call", span={"end_byte":1070,"end_column":1,"end_line":42,"start_byte":745,"start_column":1,"start_line":31}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.roast_analysis.summarize_roast_samples", phase="implementation-call", span={"end_byte":1070,"end_column":1,"end_line":42,"start_byte":745,"start_column":1,"start_line":31}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, RoastAnalysis, path="$.return")
    return _result

def analyze_roast_profile(profile: RoastProfile) -> Result[RoastAnalysis, RoastAnalysisError]:
    """Validate a roast profile, then summarize its samples without repeating
chronology checks."""
    profile = _cott_validate_abi(profile, RoastProfile, path="$.profile")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((profile).samples) == 0)):
        _expected_error = RoastAnalysisError_EmptySamples
        _expected_error_span = {"end_byte":1354,"end_column":72,"end_line":48,"start_byte":1287,"start_column":5,"start_line":48}
        _expected_error_clause = "error:1"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/roast_analysis/analyze_roast_profile.py", "d834d5213c01228eb35473777e787fc8ea03a6907e504308c0272a5f471d6ca9", "analyze_roast_profile", expected_project_name="roast-analysis", expected_cott_symbol="curriculum.roast_analysis.analyze_roast_profile")
        _result = _implementation(profile)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.roast_analysis.analyze_roast_profile"
        if _error.span is None:
            _error.span = {"end_byte":1418,"end_column":1,"end_line":52,"start_byte":1070,"start_column":1,"start_line":42}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.roast_analysis.analyze_roast_profile", phase="implementation-call", span={"end_byte":1418,"end_column":1,"end_line":52,"start_byte":1070,"start_column":1,"start_line":42}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.roast_analysis.analyze_roast_profile", phase="implementation-call", span={"end_byte":1418,"end_column":1,"end_line":52,"start_byte":1070,"start_column":1,"start_line":42}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[RoastAnalysis, RoastAnalysisError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.roast_analysis.analyze_roast_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (RoastAnalysisError_NonIncreasingTime,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.roast_analysis.analyze_roast_profile", phase="error", span={"end_byte":1418,"end_column":1,"end_line":52,"start_byte":1070,"start_column":1,"start_line":42}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.roast_analysis.analyze_roast_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    return _result

__all__ = ["RoastAnalysis", "RoastAnalysisError", "RoastAnalysisError_EmptySamples", "RoastAnalysisError_NonIncreasingTime", "RoastProfile", "TemperatureSample", "analyze_roast_profile", "summarize_roast_samples", "validate_roast_profile"]
