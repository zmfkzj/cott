from __future__ import annotations

import dataclasses as _dataclasses
from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.backup_plan_types import BackupPath, BackupPlan, BackupPlanError, BackupPlanError_BlankContentId, BackupPlanError_DuplicatePath, BackupPlanError_EmptyPath, BackupPlanRequest

def validate_backup_request(request: BackupPlanRequest) -> Result[Unit, BackupPlanError]:
    """Validate backup paths in request order. For each path, EmptyPath takes
priority over BlankContentId, which takes priority over DuplicatePath.
Duplicate detection includes every earlier valid path."""
    request = _cott_validate_abi(request, BackupPlanRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/backup_plan/validate_backup_request.py", "30354bc8b1700b825b7b084382e9722c10c40e82e0fb242b3bcad545355e076d", "validate_backup_request", expected_project_name="backup-plan", expected_cott_symbol="curriculum.backup_plan.validate_backup_request")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.backup_plan.validate_backup_request"
        if _error.span is None:
            _error.span = {"end_byte":783,"end_column":1,"end_line":33,"start_byte":330,"start_column":1,"start_line":20}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.backup_plan.validate_backup_request", phase="implementation-call", span={"end_byte":783,"end_column":1,"end_line":33,"start_byte":330,"start_column":1,"start_line":20}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.backup_plan.validate_backup_request", phase="implementation-call", span={"end_byte":783,"end_column":1,"end_line":33,"start_byte":330,"start_column":1,"start_line":20}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Unit, BackupPlanError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.backup_plan.validate_backup_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (BackupPlanError_EmptyPath, BackupPlanError_BlankContentId, BackupPlanError_DuplicatePath,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.backup_plan.validate_backup_request", phase="error", span={"end_byte":783,"end_column":1,"end_line":33,"start_byte":330,"start_column":1,"start_line":20}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.backup_plan.validate_backup_request", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    return _result

def classify_backup_paths(paths: CottList[BackupPath], known_content_ids: CottSet[str]) -> BackupPlan:
    """Classify the first occurrence of each content identifier in input order.
Known content is reused; unknown content contributes its path for upload."""
    paths = _cott_validate_abi(paths, CottList[BackupPath], path="$.paths")
    known_content_ids = _cott_validate_abi(known_content_ids, CottSet[str], path="$.known_content_ids")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/backup_plan/classify_backup_paths.py", "f5229ffd3a69be10e2de59791d5cee056623810b0d1b6406edcaa179e640fba0", "classify_backup_paths", expected_project_name="backup-plan", expected_cott_symbol="curriculum.backup_plan.classify_backup_paths")
        _result = _implementation(paths, known_content_ids)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.backup_plan.classify_backup_paths"
        if _error.span is None:
            _error.span = {"end_byte":1157,"end_column":1,"end_line":43,"start_byte":783,"start_column":1,"start_line":33}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.backup_plan.classify_backup_paths", phase="implementation-call", span={"end_byte":1157,"end_column":1,"end_line":43,"start_byte":783,"start_column":1,"start_line":33}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.backup_plan.classify_backup_paths", phase="implementation-call", span={"end_byte":1157,"end_column":1,"end_line":43,"start_byte":783,"start_column":1,"start_line":33}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, BackupPlan, path="$.return")
    if True:
        plan = _result
        if not (((len((plan).upload_paths) + len((plan).reused_content_ids)) <= len(paths))):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.backup_plan.classify_backup_paths", clause="ensures:1", phase="ensures", span={"end_byte":1139,"end_column":87,"end_line":39,"start_byte":1057,"start_column":5,"start_line":39}, expected="true", actual="false")
    return _result

def plan_backup(request: BackupPlanRequest) -> Result[BackupPlan, BackupPlanError]:
    """Validate a backup request, then classify its paths into deterministic
upload and reuse lists."""
    request = _cott_validate_abi(request, BackupPlanRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/curriculum/backup_plan/plan_backup.py", "6172cf2772ce8107d9a0a6d2c14bbc7b5341f616fc19ba3148524d42c056f129", "plan_backup", expected_project_name="backup-plan", expected_cott_symbol="curriculum.backup_plan.plan_backup")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.backup_plan.plan_backup"
        if _error.span is None:
            _error.span = {"end_byte":1603,"end_column":1,"end_line":56,"start_byte":1157,"start_column":1,"start_line":43}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.backup_plan.plan_backup", phase="implementation-call", span={"end_byte":1603,"end_column":1,"end_line":56,"start_byte":1157,"start_column":1,"start_line":43}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.backup_plan.plan_backup", phase="implementation-call", span={"end_byte":1603,"end_column":1,"end_line":56,"start_byte":1157,"start_column":1,"start_line":43}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[BackupPlan, BackupPlanError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.backup_plan.plan_backup", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (BackupPlanError_EmptyPath, BackupPlanError_BlankContentId, BackupPlanError_DuplicatePath,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.backup_plan.plan_backup", phase="error", span={"end_byte":1603,"end_column":1,"end_line":56,"start_byte":1157,"start_column":1,"start_line":43}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.backup_plan.plan_backup", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        plan = _result.value
        if not (((len((plan).upload_paths) + len((plan).reused_content_ids)) <= len((request).paths))):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.backup_plan.plan_backup", clause="ensures:1", phase="ensures", span={"end_byte":1468,"end_column":106,"end_line":49,"start_byte":1367,"start_column":5,"start_line":49}, expected="true", actual="false")
    return _result

__all__ = ["BackupPath", "BackupPlan", "BackupPlanError", "BackupPlanError_BlankContentId", "BackupPlanError_DuplicatePath", "BackupPlanError_EmptyPath", "BackupPlanRequest", "classify_backup_paths", "plan_backup", "validate_backup_request"]
