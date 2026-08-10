from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RunMetric:
    __hash__ = None
    run_id: str
    score: F64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RankingRequest:
    __hash__ = None
    runs: CottList[RunMetric]
    higher_is_better: bool

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Ranking:
    __hash__ = None
    ordered_run_ids: CottList[str]
    best_run_id: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExperimentRankingError_EmptyRuns:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExperimentRankingError_BlankRunId:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExperimentRankingError_NonFiniteScore:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ExperimentRankingError_DuplicateRunId:
    pass

ExperimentRankingError: TypeAlias = Union[ExperimentRankingError_EmptyRuns, ExperimentRankingError_BlankRunId, ExperimentRankingError_NonFiniteScore, ExperimentRankingError_DuplicateRunId]

"""Validate and deterministically order experiment runs.

Empty input is rejected first. Runs are then validated in input order;
within each run, a blank run_id is reported before a non-finite score and
before a duplicate run_id. Duplicate identifiers are compared exactly
without trimming.

When higher_is_better is true, larger scores rank first; otherwise smaller
scores rank first. Equal scores are ordered by ascending run_id. Ok
contains every input run_id exactly once."""
"""Order the request's runs with order_run_ids, propagate its first validation
error unchanged, and build a ranking whose best_run_id is the first
identifier in the successful order."""
__all__ = ["ExperimentRankingError", "ExperimentRankingError_BlankRunId", "ExperimentRankingError_DuplicateRunId", "ExperimentRankingError_EmptyRuns", "ExperimentRankingError_NonFiniteScore", "Ranking", "RankingRequest", "RunMetric"]
