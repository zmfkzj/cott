from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.experiment_ranking_types import ExperimentRankingError, ExperimentRankingError_BlankRunId, ExperimentRankingError_DuplicateRunId, ExperimentRankingError_EmptyRuns, ExperimentRankingError_NonFiniteScore, Ranking, RankingRequest, RunMetric

def order_run_ids(runs: CottList[RunMetric], higher_is_better: bool) -> Result[CottList[str], ExperimentRankingError]:
    """Validate and deterministically order experiment runs.

Empty input is rejected first. Runs are then validated in input order;
within each run, a blank run_id is reported before a non-finite score and
before a duplicate run_id. Duplicate identifiers are compared exactly
without trimming.

When higher_is_better is true, larger scores rank first; otherwise smaller
scores rank first. Equal scores are ordered by ascending run_id. Ok
contains every input run_id exactly once."""
    runs = _cott_validate_abi(runs, CottList[RunMetric], path="$.runs")
    higher_is_better = _cott_validate_abi(higher_is_better, bool, path="$.higher_is_better")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len(runs) == 0)):
        _expected_error = ExperimentRankingError_EmptyRuns
        _expected_error_span = {"end_byte":1173,"end_column":62,"end_line":41,"start_byte":1116,"start_column":5,"start_line":41}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/experiment_ranking/order_run_ids.py", "bd1182b605468ca57c0332781326bc4b2bffaba213f3c5b9fa965b1970176eac", "order_run_ids", expected_project_name="experiment-ranking", expected_cott_symbol="curriculum.experiment_ranking.order_run_ids")
        _result = _implementation(runs, higher_is_better)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.experiment_ranking.order_run_ids"
        if _error.span is None:
            _error.span = {"end_byte":1331,"end_column":1,"end_line":48,"start_byte":331,"start_column":1,"start_line":21}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.experiment_ranking.order_run_ids", phase="implementation-call", span={"end_byte":1331,"end_column":1,"end_line":48,"start_byte":331,"start_column":1,"start_line":21}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.experiment_ranking.order_run_ids", phase="implementation-call", span={"end_byte":1331,"end_column":1,"end_line":48,"start_byte":331,"start_column":1,"start_line":21}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[CottList[str], ExperimentRankingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.experiment_ranking.order_run_ids", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ExperimentRankingError_BlankRunId, ExperimentRankingError_NonFiniteScore, ExperimentRankingError_DuplicateRunId,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.experiment_ranking.order_run_ids", phase="error", span={"end_byte":1331,"end_column":1,"end_line":48,"start_byte":331,"start_column":1,"start_line":21}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.experiment_ranking.order_run_ids", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            ordered_ids = _cott_match_value.value
            return ((len(ordered_ids) == len(runs)))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.experiment_ranking.order_run_ids", clause="ensures:1", phase="ensures", span={"end_byte":1052,"end_column":66,"end_line":38,"start_byte":991,"start_column":5,"start_line":38}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            ordered_ids = _cott_match_value.value
            return ((len(ordered_ids) > 0))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.experiment_ranking.order_run_ids", clause="ensures:2", phase="ensures", span={"end_byte":1110,"end_column":58,"end_line":39,"start_byte":1057,"start_column":5,"start_line":39}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[CottList[str], ExperimentRankingError], path="$.return", validator=_cott_validate_abi)
    return _result

def rank_experiments(request: RankingRequest) -> Result[Ranking, ExperimentRankingError]:
    """Order the request's runs with order_run_ids, propagate its first validation
error unchanged, and build a ranking whose best_run_id is the first
identifier in the successful order."""
    request = _cott_validate_abi(request, RankingRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((request).runs) == 0)):
        _expected_error = ExperimentRankingError_EmptyRuns
        _expected_error_span = {"end_byte":1851,"end_column":70,"end_line":58,"start_byte":1786,"start_column":5,"start_line":58}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/experiment_ranking/rank_experiments.py", "234bfc6d5fa9a19deed947fe76700bb2561f8b5911576c89458eca142b37a24d", "rank_experiments", expected_project_name="experiment-ranking", expected_cott_symbol="curriculum.experiment_ranking.rank_experiments")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.experiment_ranking.rank_experiments"
        if _error.span is None:
            _error.span = {"end_byte":2008,"end_column":1,"end_line":64,"start_byte":1331,"start_column":1,"start_line":48}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.experiment_ranking.rank_experiments", phase="implementation-call", span={"end_byte":2008,"end_column":1,"end_line":64,"start_byte":1331,"start_column":1,"start_line":48}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.experiment_ranking.rank_experiments", phase="implementation-call", span={"end_byte":2008,"end_column":1,"end_line":64,"start_byte":1331,"start_column":1,"start_line":48}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Ranking, ExperimentRankingError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.experiment_ranking.rank_experiments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ExperimentRankingError_BlankRunId, ExperimentRankingError_NonFiniteScore, ExperimentRankingError_DuplicateRunId,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.experiment_ranking.rank_experiments", phase="error", span={"end_byte":2008,"end_column":1,"end_line":64,"start_byte":1331,"start_column":1,"start_line":48}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.experiment_ranking.rank_experiments", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            ranking = _cott_match_value.value
            return ((len((ranking).ordered_run_ids) == len((request).runs)))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.experiment_ranking.rank_experiments", clause="ensures:1", phase="ensures", span={"end_byte":1714,"end_column":82,"end_line":55,"start_byte":1637,"start_column":5,"start_line":55}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            ranking = _cott_match_value.value
            return ((len((ranking).ordered_run_ids) > 0))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.experiment_ranking.rank_experiments", clause="ensures:2", phase="ensures", span={"end_byte":1780,"end_column":66,"end_line":56,"start_byte":1719,"start_column":5,"start_line":56}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Ranking, ExperimentRankingError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["ExperimentRankingError", "ExperimentRankingError_BlankRunId", "ExperimentRankingError_DuplicateRunId", "ExperimentRankingError_EmptyRuns", "ExperimentRankingError_NonFiniteScore", "Ranking", "RankingRequest", "RunMetric", "order_run_ids", "rank_experiments"]
