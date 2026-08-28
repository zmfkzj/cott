from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CaseRecord:
    __hash__ = None
    case_id: str
    title: str
    terms: CottSet[str]
    cited_by_count: U32

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CaseRankingRequest:
    __hash__ = None
    query_terms: CottSet[str]
    cases: CottList[CaseRecord]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CaseRanking:
    __hash__ = None
    case_ids: CottList[str]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CaseRankingError_EmptyQuery:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CaseRankingError_BlankCaseId:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CaseRankingError_DuplicateCaseId:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CaseRankingError_BlankTerm:
    pass

CaseRankingError: TypeAlias = Union[CaseRankingError_EmptyQuery, CaseRankingError_BlankCaseId, CaseRankingError_DuplicateCaseId, CaseRankingError_BlankTerm]

"""Count the distinct terms shared by a query and one case. Set semantics make
every matching term contribute exactly one point. This operation is total,
including for empty sets and otherwise unvalidated records."""
"""Omit cases with no query overlap and deterministically order the remainder
by descending overlap score, descending citation count, then ascending case
identifier. Inputs need not have passed request validation."""
"""Validate a ranking request in source order, then rank its matching cases.
An empty query is rejected before blank query terms. Cases are inspected in
input order for blank identifiers, duplicate identifiers, and blank terms."""
__all__ = ["CaseRanking", "CaseRankingError", "CaseRankingError_BlankCaseId", "CaseRankingError_BlankTerm", "CaseRankingError_DuplicateCaseId", "CaseRankingError_EmptyQuery", "CaseRankingRequest", "CaseRecord"]
