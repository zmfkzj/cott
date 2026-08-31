from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.catalog_types import CatalogColumn as CatalogColumn, CatalogError as CatalogError, CatalogError_ConnectionMissing as CatalogError_ConnectionMissing, CatalogError_Failed as CatalogError_Failed, CatalogError_LimitExceeded as CatalogError_LimitExceeded, CatalogError_NamespaceMissing as CatalogError_NamespaceMissing, CatalogMatch as CatalogMatch, CatalogMatchKind as CatalogMatchKind, CatalogMatchKind_Column as CatalogMatchKind_Column, CatalogMatchKind_Relation as CatalogMatchKind_Relation, CatalogRelation as CatalogRelation, CatalogScope as CatalogScope, CatalogSnapshot as CatalogSnapshot, CompletionRequest as CompletionRequest, CompletionResult as CompletionResult, RelationKind as RelationKind, RelationKind_Table as RelationKind_Table, RelationKind_View as RelationKind_View
from real.harlequin.core_types import Connection, DatabaseTarget, SqlClientError
def catalog_relations(database: DatabaseTarget) -> Result[CottList[CatalogRelation], SqlClientError]: ...

def catalog_columns(database: DatabaseTarget, relation: str) -> Result[CottList[CatalogColumn], SqlClientError]: ...

def search_catalog(database: DatabaseTarget, term: str) -> Result[CottList[CatalogMatch], SqlClientError]: ...

def refresh_catalog(connection: Connection, scope: CatalogScope) -> Result[CatalogSnapshot, CatalogError]: ...

def complete_sql(request: CompletionRequest, snapshot: CatalogSnapshot) -> CompletionResult: ...

def find_catalog(snapshot: CatalogSnapshot, term: str, maximum_matches: U64) -> Result[CottList[CatalogMatch], CatalogError]: ...

__all__ = ["CatalogColumn", "CatalogError", "CatalogError_ConnectionMissing", "CatalogError_Failed", "CatalogError_LimitExceeded", "CatalogError_NamespaceMissing", "CatalogMatch", "CatalogMatchKind", "CatalogMatchKind_Column", "CatalogMatchKind_Relation", "CatalogRelation", "CatalogScope", "CatalogSnapshot", "CompletionRequest", "CompletionResult", "RelationKind", "RelationKind_Table", "RelationKind_View", "catalog_columns", "catalog_relations", "complete_sql", "find_catalog", "refresh_catalog", "search_catalog"]
