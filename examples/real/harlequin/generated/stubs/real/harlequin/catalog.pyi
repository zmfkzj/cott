from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.catalog_types import CatalogColumn as CatalogColumn, CatalogMatch as CatalogMatch, CatalogMatchKind as CatalogMatchKind, CatalogMatchKind_Column as CatalogMatchKind_Column, CatalogMatchKind_Relation as CatalogMatchKind_Relation, CatalogRelation as CatalogRelation, RelationKind as RelationKind, RelationKind_Table as RelationKind_Table, RelationKind_View as RelationKind_View
from real.harlequin.core_types import DatabaseTarget, SqlClientError
def catalog_relations(database: DatabaseTarget) -> Result[CottList[CatalogRelation], SqlClientError]: ...

def catalog_columns(database: DatabaseTarget, relation: str) -> Result[CottList[CatalogColumn], SqlClientError]: ...

def search_catalog(database: DatabaseTarget, term: str) -> Result[CottList[CatalogMatch], SqlClientError]: ...

__all__ = ["CatalogColumn", "CatalogMatch", "CatalogMatchKind", "CatalogMatchKind_Column", "CatalogMatchKind_Relation", "CatalogRelation", "RelationKind", "RelationKind_Table", "RelationKind_View", "catalog_columns", "catalog_relations", "search_catalog"]
