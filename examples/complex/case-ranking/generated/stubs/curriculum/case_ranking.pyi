from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.case_ranking_types import CaseRanking as CaseRanking, CaseRankingError as CaseRankingError, CaseRankingError_BlankCaseId as CaseRankingError_BlankCaseId, CaseRankingError_BlankTerm as CaseRankingError_BlankTerm, CaseRankingError_DuplicateCaseId as CaseRankingError_DuplicateCaseId, CaseRankingError_EmptyQuery as CaseRankingError_EmptyQuery, CaseRankingRequest as CaseRankingRequest, CaseRecord as CaseRecord
"""Count the distinct terms shared by a query and one case. Set semantics make
every matching term contribute exactly one point. This operation is total,
including for empty sets and otherwise unvalidated records."""
def score_case_overlap(query_terms: CottSet[str], case: CaseRecord) -> U64: ...

"""Omit cases with no query overlap and deterministically order the remainder
by descending overlap score, descending citation count, then ascending case
identifier. Inputs need not have passed request validation."""
def order_matching_cases(query_terms: CottSet[str], cases: CottList[CaseRecord]) -> CaseRanking: ...

"""Validate a ranking request in source order, then rank its matching cases.
An empty query is rejected before blank query terms. Cases are inspected in
input order for blank identifiers, duplicate identifiers, and blank terms."""
def rank_cases(request: CaseRankingRequest) -> Result[CaseRanking, CaseRankingError]: ...

__all__ = ["CaseRanking", "CaseRankingError", "CaseRankingError_BlankCaseId", "CaseRankingError_BlankTerm", "CaseRankingError_DuplicateCaseId", "CaseRankingError_EmptyQuery", "CaseRankingRequest", "CaseRecord", "order_matching_cases", "rank_cases", "score_case_overlap"]
