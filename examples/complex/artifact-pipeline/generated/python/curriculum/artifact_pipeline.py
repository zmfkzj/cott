from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_any_blank_by, _cott_cyclic_by, _cott_dependency_ordered_by, _cott_permutation_by, _cott_self_dependency_by, _cott_unique_by, _cott_unknown_dependency_by

from curriculum.artifact_pipeline_types import ArtifactPipelineError, ArtifactPipelineError_BlankStepName, ArtifactPipelineError_Cycle, ArtifactPipelineError_DuplicateStep, ArtifactPipelineError_SelfDependency, ArtifactPipelineError_UnknownDependency, ArtifactPlan, BuildStep, Pipeline

def topologically_order_steps(steps: CottList[BuildStep]) -> Result[CottList[str], ArtifactPipelineError]:
    """Validate build-step names and dependencies, then return their deterministic
topological order. Blank and duplicate names are rejected before dependency
errors. Ready steps are ordered lexicographically. A blank name is empty or
consists only of the 25 Unicode White_Space characters used by any_blank_by;
U+FEFF, U+180E, U+200B and U+001C are not whitespace for this contract."""
    steps = _cott_validate_abi(steps, CottList[BuildStep], path="$.steps")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((_cott_any_blank_by(steps, "name")), "curriculum.artifact_pipeline.topologically_order_steps", "error:4:condition")):
        _expected_error = ArtifactPipelineError_BlankStepName
        _expected_error_span = {"end_byte":1135,"end_column":87,"end_line":33,"start_byte":1053,"start_column":5,"start_line":33}
        _expected_error_clause = "error:4"
    if _expected_error is None and (_cott_contract_condition(((not _cott_unique_by(steps, "name"))), "curriculum.artifact_pipeline.topologically_order_steps", "error:5:condition")):
        _expected_error = ArtifactPipelineError_DuplicateStep
        _expected_error_span = {"end_byte":1223,"end_column":88,"end_line":34,"start_byte":1140,"start_column":5,"start_line":34}
        _expected_error_clause = "error:5"
    if _expected_error is None and (_cott_contract_condition((_cott_unknown_dependency_by(steps, "name", "needs")), "curriculum.artifact_pipeline.topologically_order_steps", "error:6:condition")):
        _expected_error = ArtifactPipelineError_UnknownDependency
        _expected_error_span = {"end_byte":1340,"end_column":117,"end_line":35,"start_byte":1228,"start_column":5,"start_line":35}
        _expected_error_clause = "error:6"
    if _expected_error is None and (_cott_contract_condition((_cott_self_dependency_by(steps, "name", "needs")), "curriculum.artifact_pipeline.topologically_order_steps", "error:7:condition")):
        _expected_error = ArtifactPipelineError_SelfDependency
        _expected_error_span = {"end_byte":1451,"end_column":111,"end_line":36,"start_byte":1345,"start_column":5,"start_line":36}
        _expected_error_clause = "error:7"
    if _expected_error is None and (_cott_contract_condition((_cott_cyclic_by(steps, "name", "needs")), "curriculum.artifact_pipeline.topologically_order_steps", "error:8:condition")):
        _expected_error = ArtifactPipelineError_Cycle
        _expected_error_span = {"end_byte":1544,"end_column":93,"end_line":37,"start_byte":1456,"start_column":5,"start_line":37}
        _expected_error_clause = "error:8"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/artifact_pipeline/topologically_order_steps.py", "9a0085d4618094b0a3705ea6639019fe372c7ddf420df912383ae6dbc5259a52", "topologically_order_steps", expected_project_name="artifact-pipeline", expected_cott_symbol="curriculum.artifact_pipeline.topologically_order_steps")
        _result = _implementation(steps)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.artifact_pipeline.topologically_order_steps"
        if _error.span is None:
            _error.span = {"end_byte":1562,"end_column":1,"end_line":41,"start_byte":302,"start_column":1,"start_line":20}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.artifact_pipeline.topologically_order_steps", phase="implementation-call", span={"end_byte":1562,"end_column":1,"end_line":41,"start_byte":302,"start_column":1,"start_line":20}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.artifact_pipeline.topologically_order_steps", phase="implementation-call", span={"end_byte":1562,"end_column":1,"end_line":41,"start_byte":302,"start_column":1,"start_line":20}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], ArtifactPipelineError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.artifact_pipeline.topologically_order_steps", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.artifact_pipeline.topologically_order_steps", phase="error", span={"end_byte":1562,"end_column":1,"end_line":41,"start_byte":302,"start_column":1,"start_line":20}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.artifact_pipeline.topologically_order_steps", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.topologically_order_steps", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            ordered_steps = _cott_match_value.value
            return (_cott_contract_condition((_cott_permutation_by(ordered_steps, steps, "name")), "curriculum.artifact_pipeline.topologically_order_steps", "ensures:1"))
        _cott_contract_condition((False), "curriculum.artifact_pipeline.topologically_order_steps", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.artifact_pipeline.topologically_order_steps", clause="ensures:1", phase="ensures", span={"end_byte":910,"end_column":93,"end_line":29,"start_byte":822,"start_column":5,"start_line":29}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            ordered_steps = _cott_match_value.value
            return (_cott_contract_condition((_cott_dependency_ordered_by(ordered_steps, steps, "name", "needs")), "curriculum.artifact_pipeline.topologically_order_steps", "ensures:2"))
        _cott_contract_condition((False), "curriculum.artifact_pipeline.topologically_order_steps", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.artifact_pipeline.topologically_order_steps", clause="ensures:2", phase="ensures", span={"end_byte":1027,"end_column":117,"end_line":30,"start_byte":915,"start_column":5,"start_line":30}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], ArtifactPipelineError], path="$.return", validator=_cott_validate_abi)
    return _result

def plan_pipeline(pipeline: Pipeline) -> Result[ArtifactPlan, ArtifactPipelineError]:
    """Order and validate the pipeline's build steps with topologically_order_steps
and construct an artifact plan, propagating any ordering error unchanged."""
    pipeline = _cott_validate_abi(pipeline, Pipeline, path="$.pipeline")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (_cott_contract_condition((_cott_any_blank_by((pipeline).steps, "name")), "curriculum.artifact_pipeline.plan_pipeline", "error:4:condition")):
        _expected_error = ArtifactPipelineError_BlankStepName
        _expected_error_span = {"end_byte":2163,"end_column":96,"end_line":51,"start_byte":2072,"start_column":5,"start_line":51}
        _expected_error_clause = "error:4"
    if _expected_error is None and (_cott_contract_condition(((not _cott_unique_by((pipeline).steps, "name"))), "curriculum.artifact_pipeline.plan_pipeline", "error:5:condition")):
        _expected_error = ArtifactPipelineError_DuplicateStep
        _expected_error_span = {"end_byte":2260,"end_column":97,"end_line":52,"start_byte":2168,"start_column":5,"start_line":52}
        _expected_error_clause = "error:5"
    if _expected_error is None and (_cott_contract_condition((_cott_unknown_dependency_by((pipeline).steps, "name", "needs")), "curriculum.artifact_pipeline.plan_pipeline", "error:6:condition")):
        _expected_error = ArtifactPipelineError_UnknownDependency
        _expected_error_span = {"end_byte":2386,"end_column":126,"end_line":53,"start_byte":2265,"start_column":5,"start_line":53}
        _expected_error_clause = "error:6"
    if _expected_error is None and (_cott_contract_condition((_cott_self_dependency_by((pipeline).steps, "name", "needs")), "curriculum.artifact_pipeline.plan_pipeline", "error:7:condition")):
        _expected_error = ArtifactPipelineError_SelfDependency
        _expected_error_span = {"end_byte":2506,"end_column":120,"end_line":54,"start_byte":2391,"start_column":5,"start_line":54}
        _expected_error_clause = "error:7"
    if _expected_error is None and (_cott_contract_condition((_cott_cyclic_by((pipeline).steps, "name", "needs")), "curriculum.artifact_pipeline.plan_pipeline", "error:8:condition")):
        _expected_error = ArtifactPipelineError_Cycle
        _expected_error_span = {"end_byte":2608,"end_column":102,"end_line":55,"start_byte":2511,"start_column":5,"start_line":55}
        _expected_error_clause = "error:8"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/artifact_pipeline/plan_pipeline.py", "46b7e60d4738490b0f8bd84d385fbacb25949b4e7565ff630e282fe3586cbf3f", "plan_pipeline", expected_project_name="artifact-pipeline", expected_cott_symbol="curriculum.artifact_pipeline.plan_pipeline")
        _result = _implementation(pipeline)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.artifact_pipeline.plan_pipeline"
        if _error.span is None:
            _error.span = {"end_byte":2626,"end_column":1,"end_line":59,"start_byte":1562,"start_column":1,"start_line":41}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.artifact_pipeline.plan_pipeline", phase="implementation-call", span={"end_byte":2626,"end_column":1,"end_line":59,"start_byte":1562,"start_column":1,"start_line":41}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.artifact_pipeline.plan_pipeline", phase="implementation-call", span={"end_byte":2626,"end_column":1,"end_line":59,"start_byte":1562,"start_column":1,"start_line":41}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[ArtifactPlan, ArtifactPipelineError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.artifact_pipeline.plan_pipeline", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.artifact_pipeline.plan_pipeline", phase="error", span={"end_byte":2626,"end_column":1,"end_line":59,"start_byte":1562,"start_column":1,"start_line":41}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.artifact_pipeline.plan_pipeline", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "curriculum.artifact_pipeline.plan_pipeline", _expected_error_clause)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition((_cott_permutation_by((plan).ordered_steps, (pipeline).steps, "name")), "curriculum.artifact_pipeline.plan_pipeline", "ensures:1"))
        _cott_contract_condition((False), "curriculum.artifact_pipeline.plan_pipeline", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.artifact_pipeline.plan_pipeline", clause="ensures:1", phase="ensures", span={"end_byte":1924,"end_column":98,"end_line":47,"start_byte":1831,"start_column":5,"start_line":47}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            plan = _cott_match_value.value
            return (_cott_contract_condition((_cott_dependency_ordered_by((plan).ordered_steps, (pipeline).steps, "name", "needs")), "curriculum.artifact_pipeline.plan_pipeline", "ensures:2"))
        _cott_contract_condition((False), "curriculum.artifact_pipeline.plan_pipeline", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.artifact_pipeline.plan_pipeline", clause="ensures:2", phase="ensures", span={"end_byte":2046,"end_column":122,"end_line":48,"start_byte":1929,"start_column":5,"start_line":48}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ArtifactPlan, ArtifactPipelineError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["ArtifactPipelineError", "ArtifactPipelineError_BlankStepName", "ArtifactPipelineError_Cycle", "ArtifactPipelineError_DuplicateStep", "ArtifactPipelineError_SelfDependency", "ArtifactPipelineError_UnknownDependency", "ArtifactPlan", "BuildStep", "Pipeline", "plan_pipeline", "topologically_order_steps"]
