from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from real.harlequin.core_types import Connection, DatabaseTarget, SqlClientError

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RelationKind_Table:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RelationKind_View:
    pass

RelationKind: TypeAlias = Union[RelationKind_Table, RelationKind_View]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogMatchKind_Relation:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogMatchKind_Column:
    pass

CatalogMatchKind: TypeAlias = Union[CatalogMatchKind_Relation, CatalogMatchKind_Column]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogRelation:
    __hash__ = None
    name: str
    kind: RelationKind
    sql: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, RelationKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "sql", _cott_validate_abi(self.sql, Option[str], path="$.sql"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogColumn:
    __hash__ = None
    relation: str
    ordinal: U32
    name: str
    declared_type: str
    not_null: bool
    default_sql: Option[str]
    primary_key_position: U32

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "relation", _cott_validate_abi(self.relation, str, path="$.relation"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ordinal", _cott_validate_abi(self.ordinal, U32, path="$.ordinal"))
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "declared_type", _cott_validate_abi(self.declared_type, str, path="$.declared_type"))
        if not _cott_validated_construction():
            object.__setattr__(self, "not_null", _cott_validate_abi(self.not_null, bool, path="$.not_null"))
        if not _cott_validated_construction():
            object.__setattr__(self, "default_sql", _cott_validate_abi(self.default_sql, Option[str], path="$.default_sql"))
        if not _cott_validated_construction():
            object.__setattr__(self, "primary_key_position", _cott_validate_abi(self.primary_key_position, U32, path="$.primary_key_position"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogMatch:
    __hash__ = None
    kind: CatalogMatchKind
    relation: str
    name: str
    ordinal: U32

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "kind", _cott_validate_abi(self.kind, CatalogMatchKind, path="$.kind"))
        if not _cott_validated_construction():
            object.__setattr__(self, "relation", _cott_validate_abi(self.relation, str, path="$.relation"))
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ordinal", _cott_validate_abi(self.ordinal, U32, path="$.ordinal"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogScope:
    __hash__ = None
    connection_id: str
    namespace: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "connection_id", _cott_validate_abi(self.connection_id, str, path="$.connection_id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "namespace", _cott_validate_abi(self.namespace, Option[str], path="$.namespace"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogSnapshot:
    __hash__ = None
    scope: CatalogScope
    relations: CottList[CatalogRelation]
    refreshed_at: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "scope", _cott_validate_abi(self.scope, CatalogScope, path="$.scope"))
        if not _cott_validated_construction():
            object.__setattr__(self, "relations", _cott_validate_abi(self.relations, CottList[CatalogRelation], path="$.relations"))
        if not _cott_validated_construction():
            object.__setattr__(self, "refreshed_at", _cott_validate_abi(self.refreshed_at, str, path="$.refreshed_at"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CompletionRequest:
    __hash__ = None
    source: str
    cursor: U64
    scope: CatalogScope
    maximum_candidates: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "source", _cott_validate_abi(self.source, str, path="$.source"))
        if not _cott_validated_construction():
            object.__setattr__(self, "cursor", _cott_validate_abi(self.cursor, U64, path="$.cursor"))
        if not _cott_validated_construction():
            object.__setattr__(self, "scope", _cott_validate_abi(self.scope, CatalogScope, path="$.scope"))
        if not _cott_validated_construction():
            object.__setattr__(self, "maximum_candidates", _cott_validate_abi(self.maximum_candidates, U64, path="$.maximum_candidates"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CompletionResult:
    __hash__ = None
    candidates: CottList[str]
    replace_start: U64
    replace_end: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "candidates", _cott_validate_abi(self.candidates, CottList[str], path="$.candidates"))
        if not _cott_validated_construction():
            object.__setattr__(self, "replace_start", _cott_validate_abi(self.replace_start, U64, path="$.replace_start"))
        if not _cott_validated_construction():
            object.__setattr__(self, "replace_end", _cott_validate_abi(self.replace_end, U64, path="$.replace_end"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogError_ConnectionMissing:
    __hash__ = None
    connection_id: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogError_NamespaceMissing:
    __hash__ = None
    namespace: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogError_Failed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CatalogError_LimitExceeded:
    __hash__ = None
    limit: U32

CatalogError: TypeAlias = Union[CatalogError_ConnectionMissing, CatalogError_NamespaceMissing, CatalogError_Failed, CatalogError_LimitExceeded]

__all__ = ["CatalogColumn", "CatalogError", "CatalogError_ConnectionMissing", "CatalogError_Failed", "CatalogError_LimitExceeded", "CatalogError_NamespaceMissing", "CatalogMatch", "CatalogMatchKind", "CatalogMatchKind_Column", "CatalogMatchKind_Relation", "CatalogRelation", "CatalogScope", "CatalogSnapshot", "CompletionRequest", "CompletionResult", "RelationKind", "RelationKind_Table", "RelationKind_View"]
