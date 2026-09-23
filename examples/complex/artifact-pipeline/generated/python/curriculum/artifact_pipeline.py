from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from curriculum.artifact_pipeline_types import ArtifactPipelineError, ArtifactPipelineError_BlankStepName, ArtifactPipelineError_Cycle, ArtifactPipelineError_DuplicateStep, ArtifactPipelineError_SelfDependency, ArtifactPipelineError_UnknownDependency, ArtifactPlan, BuildStep, Pipeline

def topologically_order_steps(steps: CottList[BuildStep]) -> Result[CottList[str], ArtifactPipelineError]:
    """Validate build-step names and dependencies, then return their deterministic
topological order. Blank and duplicate names are rejected before dependency
errors. Ready steps are ordered lexicographically."""
    steps = _cott_validate_abi(steps, CottList[BuildStep], path="$.steps")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/artifact_pipeline/topologically_order_steps.py", "1d3ed05e28dad97fe43cd8dea009e9dd52b58831cf262b5ac583b1b500ae5cce", "topologically_order_steps", expected_project_name="artifact-pipeline", expected_cott_symbol="curriculum.artifact_pipeline.topologically_order_steps")
        _result = _implementation(steps)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.artifact_pipeline.topologically_order_steps"
        if _error.span is None:
            _error.span = {"end_byte":952,"end_column":1,"end_line":37,"start_byte":302,"start_column":1,"start_line":20}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.artifact_pipeline.topologically_order_steps", phase="implementation-call", span={"end_byte":952,"end_column":1,"end_line":37,"start_byte":302,"start_column":1,"start_line":20}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.artifact_pipeline.topologically_order_steps", phase="implementation-call", span={"end_byte":952,"end_column":1,"end_line":37,"start_byte":302,"start_column":1,"start_line":20}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], ArtifactPipelineError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.artifact_pipeline.topologically_order_steps", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ArtifactPipelineError_BlankStepName, ArtifactPipelineError_DuplicateStep, ArtifactPipelineError_UnknownDependency, ArtifactPipelineError_SelfDependency, ArtifactPipelineError_Cycle,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.artifact_pipeline.topologically_order_steps", phase="error", span={"end_byte":952,"end_column":1,"end_line":37,"start_byte":302,"start_column":1,"start_line":20}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.artifact_pipeline.topologically_order_steps", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.topologically_order_steps", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ArtifactPipelineError_BlankStepName:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.topologically_order_steps", "error:2")
    if type(_result) is Err and type(_result.error) is ArtifactPipelineError_DuplicateStep:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.topologically_order_steps", "error:3")
    if type(_result) is Err and type(_result.error) is ArtifactPipelineError_UnknownDependency:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.topologically_order_steps", "error:4")
    if type(_result) is Err and type(_result.error) is ArtifactPipelineError_SelfDependency:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.topologically_order_steps", "error:5")
    if type(_result) is Err and type(_result.error) is ArtifactPipelineError_Cycle:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.topologically_order_steps", "error:6")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            ordered_steps = _cott_match_value.value
            return (_cott_contract_condition(((len(ordered_steps) == len(steps))), "curriculum.artifact_pipeline.topologically_order_steps", "ensures:1"))
        _cott_contract_condition((False), "curriculum.artifact_pipeline.topologically_order_steps", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.artifact_pipeline.topologically_order_steps", clause="ensures:1", phase="ensures", span={"end_byte":706,"end_column":71,"end_line":27,"start_byte":640,"start_column":5,"start_line":27}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], ArtifactPipelineError], path="$.return", validator=_cott_validate_abi)
    return _result

def plan_pipeline(pipeline: Pipeline) -> Result[ArtifactPlan, ArtifactPipelineError]:
    """Order and validate the pipeline's build steps with topologically_order_steps
and construct an artifact plan, propagating any ordering error unchanged."""
    pipeline = _cott_validate_abi(pipeline, Pipeline, path="$.pipeline")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/artifact_pipeline/plan_pipeline.py", "46b7e60d4738490b0f8bd84d385fbacb25949b4e7565ff630e282fe3586cbf3f", "plan_pipeline", expected_project_name="artifact-pipeline", expected_cott_symbol="curriculum.artifact_pipeline.plan_pipeline")
        _result = _implementation(pipeline)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.artifact_pipeline.plan_pipeline"
        if _error.span is None:
            _error.span = {"end_byte":1537,"end_column":1,"end_line":52,"start_byte":952,"start_column":1,"start_line":37}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.artifact_pipeline.plan_pipeline", phase="implementation-call", span={"end_byte":1537,"end_column":1,"end_line":52,"start_byte":952,"start_column":1,"start_line":37}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.artifact_pipeline.plan_pipeline", phase="implementation-call", span={"end_byte":1537,"end_column":1,"end_line":52,"start_byte":952,"start_column":1,"start_line":37}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ArtifactPlan, ArtifactPipelineError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.artifact_pipeline.plan_pipeline", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ArtifactPipelineError_BlankStepName, ArtifactPipelineError_DuplicateStep, ArtifactPipelineError_UnknownDependency, ArtifactPipelineError_SelfDependency, ArtifactPipelineError_Cycle,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.artifact_pipeline.plan_pipeline", phase="error", span={"end_byte":1537,"end_column":1,"end_line":52,"start_byte":952,"start_column":1,"start_line":37}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.artifact_pipeline.plan_pipeline", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.plan_pipeline", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ArtifactPipelineError_BlankStepName:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.plan_pipeline", "error:2")
    if type(_result) is Err and type(_result.error) is ArtifactPipelineError_DuplicateStep:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.plan_pipeline", "error:3")
    if type(_result) is Err and type(_result.error) is ArtifactPipelineError_UnknownDependency:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.plan_pipeline", "error:4")
    if type(_result) is Err and type(_result.error) is ArtifactPipelineError_SelfDependency:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.plan_pipeline", "error:5")
    if type(_result) is Err and type(_result.error) is ArtifactPipelineError_Cycle:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.plan_pipeline", "error:6")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition(((len((plan).ordered_steps) == len((pipeline).steps))), "curriculum.artifact_pipeline.plan_pipeline", "ensures:1"))
        _cott_contract_condition((False), "curriculum.artifact_pipeline.plan_pipeline", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.artifact_pipeline.plan_pipeline", clause="ensures:1", phase="ensures", span={"end_byte":1292,"end_column":76,"end_line":43,"start_byte":1221,"start_column":5,"start_line":43}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ArtifactPlan, ArtifactPipelineError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["ArtifactPipelineError", "ArtifactPipelineError_BlankStepName", "ArtifactPipelineError_Cycle", "ArtifactPipelineError_DuplicateStep", "ArtifactPipelineError_SelfDependency", "ArtifactPipelineError_UnknownDependency", "ArtifactPlan", "BuildStep", "Pipeline", "plan_pipeline", "topologically_order_steps"]
