from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.compute_iou_types import Box, IntersectionUnion, IouError, IouError_AreaOverflow, IouError_InvalidGroundTruthBox, IouError_InvalidPredictedBox, IouError_NonFiniteOutput, IouError_ZeroUnion

def calculate_intersection_union(ground_truth: Box, predicted: Box) -> Result[IntersectionUnion, IouError]:
    """Validates two inclusive-pixel boxes and returns their intersection and union
areas. Each width and height is maximum minus minimum plus one. Overlap
dimensions are clamped to zero, so disjoint boxes have zero intersection.
Union is the sum of both box areas minus the intersection.

Errors are selected in this order: InvalidGroundTruthBox,
InvalidPredictedBox, AreaOverflow when either box area or the union exceeds
9223372036854775807, then ZeroUnion. Every successful intersection is
non-negative, and every successful union is positive and fits in I64."""
    ground_truth = _cott_validate_abi(ground_truth, Box, path="$.ground_truth")
    predicted = _cott_validate_abi(predicted, Box, path="$.predicted")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((((ground_truth).xmin > (ground_truth).xmax) or ((ground_truth).ymin > (ground_truth).ymax))):
        _expected_error = IouError_InvalidGroundTruthBox
        _expected_error_span = {"end_byte":1139,"end_column":127,"end_line":36,"start_byte":1017,"start_column":5,"start_line":36}
        _expected_error_clause = "error:1"
    if _expected_error is None and ((((predicted).xmin > (predicted).xmax) or ((predicted).ymin > (predicted).ymax))):
        _expected_error = IouError_InvalidPredictedBox
        _expected_error_span = {"end_byte":1252,"end_column":113,"end_line":37,"start_byte":1144,"start_column":5,"start_line":37}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/compute_iou/calculate_intersection_union.py", "0a0c6b570b22490e1b85e21a4c3da82503c768426c1799936d53bb738cbfa7d8", "calculate_intersection_union", expected_project_name="compute-iou", expected_cott_symbol="curriculum.compute_iou.calculate_intersection_union")
        _result = _implementation(ground_truth, predicted)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.compute_iou.calculate_intersection_union"
        if _error.span is None:
            _error.span = {"end_byte":1315,"end_column":1,"end_line":41,"start_byte":281,"start_column":1,"start_line":20}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.compute_iou.calculate_intersection_union", phase="implementation-call", span={"end_byte":1315,"end_column":1,"end_line":41,"start_byte":281,"start_column":1,"start_line":20}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.compute_iou.calculate_intersection_union", phase="implementation-call", span={"end_byte":1315,"end_column":1,"end_line":41,"start_byte":281,"start_column":1,"start_line":20}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[IntersectionUnion, IouError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.compute_iou.calculate_intersection_union", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (IouError_AreaOverflow, IouError_ZeroUnion,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.compute_iou.calculate_intersection_union", phase="error", span={"end_byte":1315,"end_column":1,"end_line":41,"start_byte":281,"start_column":1,"start_line":20}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.compute_iou.calculate_intersection_union", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    _result = _cott_wrap_async_protocol(_result, Result[IntersectionUnion, IouError], path="$.return", validator=_cott_validate_abi)
    return _result

def compute_iou(ground_truth: Box, predicted: Box) -> Result[F64, IouError]:
    """Calls calculate_intersection_union and propagates its errors unchanged, then
divides the intersection by the union. Disjoint boxes return Ok(0.0).
NonFiniteOutput is returned if the division is not finite; every successful
result lies in [0.0, 1.0]."""
    ground_truth = _cott_validate_abi(ground_truth, Box, path="$.ground_truth")
    predicted = _cott_validate_abi(predicted, Box, path="$.predicted")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((((ground_truth).xmin > (ground_truth).xmax) or ((ground_truth).ymin > (ground_truth).ymax))):
        _expected_error = IouError_InvalidGroundTruthBox
        _expected_error_span = {"end_byte":1804,"end_column":127,"end_line":49,"start_byte":1682,"start_column":5,"start_line":49}
        _expected_error_clause = "error:1"
    if _expected_error is None and ((((predicted).xmin > (predicted).xmax) or ((predicted).ymin > (predicted).ymax))):
        _expected_error = IouError_InvalidPredictedBox
        _expected_error_span = {"end_byte":1917,"end_column":113,"end_line":50,"start_byte":1809,"start_column":5,"start_line":50}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/compute_iou/compute_iou.py", "3033de91f8227e1cccd2b790fd0c86bd104e3cbcdcd35dcea7a160af7a2e6244", "compute_iou", expected_project_name="compute-iou", expected_cott_symbol="curriculum.compute_iou.compute_iou")
        _result = _implementation(ground_truth, predicted)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.compute_iou.compute_iou"
        if _error.span is None:
            _error.span = {"end_byte":2014,"end_column":1,"end_line":54,"start_byte":1315,"start_column":1,"start_line":41}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.compute_iou.compute_iou", phase="implementation-call", span={"end_byte":2014,"end_column":1,"end_line":54,"start_byte":1315,"start_column":1,"start_line":41}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.compute_iou.compute_iou", phase="implementation-call", span={"end_byte":2014,"end_column":1,"end_line":54,"start_byte":1315,"start_column":1,"start_line":41}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[F64, IouError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.compute_iou.compute_iou", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (IouError_AreaOverflow, IouError_ZeroUnion, IouError_NonFiniteOutput,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.compute_iou.compute_iou", phase="error", span={"end_byte":2014,"end_column":1,"end_line":54,"start_byte":1315,"start_column":1,"start_line":41}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.compute_iou.compute_iou", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    _result = _cott_wrap_async_protocol(_result, Result[F64, IouError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["Box", "IntersectionUnion", "IouError", "IouError_AreaOverflow", "IouError_InvalidGroundTruthBox", "IouError_InvalidPredictedBox", "IouError_NonFiniteOutput", "IouError_ZeroUnion", "calculate_intersection_union", "compute_iou"]
