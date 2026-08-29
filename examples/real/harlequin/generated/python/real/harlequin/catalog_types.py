from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from real.harlequin.core_types import DatabaseTarget, SqlClientError

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

__all__ = ["CatalogColumn", "CatalogMatch", "CatalogMatchKind", "CatalogMatchKind_Column", "CatalogMatchKind_Relation", "CatalogRelation", "RelationKind", "RelationKind_Table", "RelationKind_View"]
