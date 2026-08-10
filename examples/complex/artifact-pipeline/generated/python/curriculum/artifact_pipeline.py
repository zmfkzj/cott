from __future__ import annotations

import dataclasses as _dataclasses
from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

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
        _implementation = _cott_load("_cott_impl/curriculum/artifact_pipeline/topologically_order_steps.py", "75cd641bcc9533d75efed41bd2c8b2c4fd8040aed0ace98727cce9ac8e77da7c", "topologically_order_steps", expected_project_name="artifact-pipeline", expected_cott_symbol="curriculum.artifact_pipeline.topologically_order_steps")
        _result = _implementation(steps)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.artifact_pipeline.topologically_order_steps"
        if _error.span is None:
            _error.span = {"end_byte":953,"end_column":1,"end_line":37,"start_byte":303,"start_column":1,"start_line":20}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.artifact_pipeline.topologically_order_steps", phase="implementation-call", span={"end_byte":953,"end_column":1,"end_line":37,"start_byte":303,"start_column":1,"start_line":20}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.artifact_pipeline.topologically_order_steps", phase="implementation-call", span={"end_byte":953,"end_column":1,"end_line":37,"start_byte":303,"start_column":1,"start_line":20}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], ArtifactPipelineError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.artifact_pipeline.topologically_order_steps", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ArtifactPipelineError_BlankStepName, ArtifactPipelineError_DuplicateStep, ArtifactPipelineError_UnknownDependency, ArtifactPipelineError_SelfDependency, ArtifactPipelineError_Cycle,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.artifact_pipeline.topologically_order_steps", phase="error", span={"end_byte":953,"end_column":1,"end_line":37,"start_byte":303,"start_column":1,"start_line":20}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.artifact_pipeline.topologically_order_steps", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        ordered_steps = _result.value
        if not ((len(ordered_steps) == len(steps))):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.artifact_pipeline.topologically_order_steps", clause="ensures:1", phase="ensures", span={"end_byte":707,"end_column":71,"end_line":27,"start_byte":641,"start_column":5,"start_line":27}, expected="true", actual="false")
    return _result

def plan_pipeline(pipeline: Pipeline) -> Result[ArtifactPlan, ArtifactPipelineError]:
    """Order and validate the pipeline's build steps with topologically_order_steps
and construct an artifact plan, propagating any ordering error unchanged."""
    pipeline = _cott_validate_abi(pipeline, Pipeline, path="$.pipeline")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/artifact_pipeline/plan_pipeline.py", "58846d410e11e424a80280c76e3b7070040b927f773ac2cd1bc6eb15a058369a", "plan_pipeline", expected_project_name="artifact-pipeline", expected_cott_symbol="curriculum.artifact_pipeline.plan_pipeline")
        _result = _implementation(pipeline)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.artifact_pipeline.plan_pipeline"
        if _error.span is None:
            _error.span = {"end_byte":1538,"end_column":1,"end_line":52,"start_byte":953,"start_column":1,"start_line":37}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.artifact_pipeline.plan_pipeline", phase="implementation-call", span={"end_byte":1538,"end_column":1,"end_line":52,"start_byte":953,"start_column":1,"start_line":37}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.artifact_pipeline.plan_pipeline", phase="implementation-call", span={"end_byte":1538,"end_column":1,"end_line":52,"start_byte":953,"start_column":1,"start_line":37}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ArtifactPlan, ArtifactPipelineError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.artifact_pipeline.plan_pipeline", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ArtifactPipelineError_BlankStepName, ArtifactPipelineError_DuplicateStep, ArtifactPipelineError_UnknownDependency, ArtifactPipelineError_SelfDependency, ArtifactPipelineError_Cycle,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.artifact_pipeline.plan_pipeline", phase="error", span={"end_byte":1538,"end_column":1,"end_line":52,"start_byte":953,"start_column":1,"start_line":37}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.artifact_pipeline.plan_pipeline", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        plan = _result.value
        if not ((len((plan).ordered_steps) == len((pipeline).steps))):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.artifact_pipeline.plan_pipeline", clause="ensures:1", phase="ensures", span={"end_byte":1293,"end_column":76,"end_line":43,"start_byte":1222,"start_column":5,"start_line":43}, expected="true", actual="false")
    return _result

__all__ = ["ArtifactPipelineError", "ArtifactPipelineError_BlankStepName", "ArtifactPipelineError_Cycle", "ArtifactPipelineError_DuplicateStep", "ArtifactPipelineError_SelfDependency", "ArtifactPipelineError_UnknownDependency", "ArtifactPlan", "BuildStep", "Pipeline", "plan_pipeline", "topologically_order_steps"]
