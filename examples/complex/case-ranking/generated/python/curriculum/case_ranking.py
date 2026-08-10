from __future__ import annotations

import dataclasses as _dataclasses
from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.case_ranking_types import CaseRanking, CaseRankingError, CaseRankingError_BlankCaseId, CaseRankingError_BlankTerm, CaseRankingError_DuplicateCaseId, CaseRankingError_EmptyQuery, CaseRankingRequest, CaseRecord

def score_case_overlap(query_terms: CottSet[str], case: CaseRecord) -> U64:
    """Count the distinct terms shared by a query and one case. Set semantics make
every matching term contribute exactly one point. This operation is total,
including for empty sets and otherwise unvalidated records."""
    query_terms = _cott_validate_abi(query_terms, CottSet[str], path="$.query_terms")
    case = _cott_validate_abi(case, CaseRecord, path="$.case")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/case_ranking/score_case_overlap.py", "d4bfa3af819b0a17a0f827c01fa4f206d83aac0dc89c93b4ad02c3ab02339faa", "score_case_overlap", expected_project_name="case-ranking", expected_cott_symbol="curriculum.case_ranking.score_case_overlap")
        _result = _implementation(query_terms, case)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.case_ranking.score_case_overlap"
        if _error.span is None:
            _error.span = {"end_byte":751,"end_column":1,"end_line":34,"start_byte":344,"start_column":1,"start_line":22}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.case_ranking.score_case_overlap", phase="implementation-call", span={"end_byte":751,"end_column":1,"end_line":34,"start_byte":344,"start_column":1,"start_line":22}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.case_ranking.score_case_overlap", phase="implementation-call", span={"end_byte":751,"end_column":1,"end_line":34,"start_byte":344,"start_column":1,"start_line":22}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, U64, path="$.return")
    if not ((_result <= len(query_terms))):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.case_ranking.score_case_overlap", clause="ensures:1", phase="ensures", span={"end_byte":696,"end_column":38,"end_line":29,"start_byte":663,"start_column":5,"start_line":29}, expected="true", actual="false")
    if not ((_result <= len((case).terms))):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.case_ranking.score_case_overlap", clause="ensures:2", phase="ensures", span={"end_byte":733,"end_column":37,"end_line":30,"start_byte":701,"start_column":5,"start_line":30}, expected="true", actual="false")
    return _result

def order_matching_cases(query_terms: CottSet[str], cases: CottList[CaseRecord]) -> CaseRanking:
    """Omit cases with no query overlap and deterministically order the remainder
by descending overlap score, descending citation count, then ascending case
identifier. Inputs need not have passed request validation."""
    query_terms = _cott_validate_abi(query_terms, CottSet[str], path="$.query_terms")
    cases = _cott_validate_abi(cases, CottList[CaseRecord], path="$.cases")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/case_ranking/order_matching_cases.py", "36040aa432b8558d8d078e6f7e8aa6f1f24b653c028a6380f0bdb682baabd4f2", "order_matching_cases", expected_project_name="case-ranking", expected_cott_symbol="curriculum.case_ranking.order_matching_cases")
        _result = _implementation(query_terms, cases)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.case_ranking.order_matching_cases"
        if _error.span is None:
            _error.span = {"end_byte":1145,"end_column":1,"end_line":45,"start_byte":751,"start_column":1,"start_line":34}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.case_ranking.order_matching_cases", phase="implementation-call", span={"end_byte":1145,"end_column":1,"end_line":45,"start_byte":751,"start_column":1,"start_line":34}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.case_ranking.order_matching_cases", phase="implementation-call", span={"end_byte":1145,"end_column":1,"end_line":45,"start_byte":751,"start_column":1,"start_line":34}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CaseRanking, path="$.return")
    if not ((len((_result).case_ids) <= len(cases))):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.case_ranking.order_matching_cases", clause="ensures:1", phase="ensures", span={"end_byte":1127,"end_column":45,"end_line":41,"start_byte":1087,"start_column":5,"start_line":41}, expected="true", actual="false")
    return _result

def rank_cases(request: CaseRankingRequest) -> Result[CaseRanking, CaseRankingError]:
    """Validate a ranking request in source order, then rank its matching cases.
An empty query is rejected before blank query terms. Cases are inspected in
input order for blank identifiers, duplicate identifiers, and blank terms."""
    request = _cott_validate_abi(request, CaseRankingRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((request).query_terms) == 0)):
        _expected_error = CaseRankingError_EmptyQuery
        _expected_error_span = {"end_byte":1636,"end_column":72,"end_line":54,"start_byte":1569,"start_column":5,"start_line":54}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/case_ranking/rank_cases.py", "949d07a1d312c27a0ae4ce048c8f4b8a425fd3c30a646a50d5cd132955f61b08", "rank_cases", expected_project_name="case-ranking", expected_cott_symbol="curriculum.case_ranking.rank_cases")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.case_ranking.rank_cases"
        if _error.span is None:
            _error.span = {"end_byte":1772,"end_column":1,"end_line":60,"start_byte":1145,"start_column":1,"start_line":45}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.case_ranking.rank_cases", phase="implementation-call", span={"end_byte":1772,"end_column":1,"end_line":60,"start_byte":1145,"start_column":1,"start_line":45}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.case_ranking.rank_cases", phase="implementation-call", span={"end_byte":1772,"end_column":1,"end_line":60,"start_byte":1145,"start_column":1,"start_line":45}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CaseRanking, CaseRankingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.case_ranking.rank_cases", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (CaseRankingError_BlankCaseId, CaseRankingError_DuplicateCaseId, CaseRankingError_BlankTerm,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.case_ranking.rank_cases", phase="error", span={"end_byte":1772,"end_column":1,"end_line":60,"start_byte":1145,"start_column":1,"start_line":45}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.case_ranking.rank_cases", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        ranking = _result.value
        if not ((len((ranking).case_ids) <= len((request).cases))):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.case_ranking.rank_cases", clause="ensures:1", phase="ensures", span={"end_byte":1563,"end_column":76,"end_line":52,"start_byte":1492,"start_column":5,"start_line":52}, expected="true", actual="false")
    return _result

__all__ = ["CaseRanking", "CaseRankingError", "CaseRankingError_BlankCaseId", "CaseRankingError_BlankTerm", "CaseRankingError_DuplicateCaseId", "CaseRankingError_EmptyQuery", "CaseRankingRequest", "CaseRecord", "order_matching_cases", "rank_cases", "score_case_overlap"]
