from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit
from real.harlequin.catalog_types import CatalogColumn, CatalogMatch, CatalogRelation
from real.harlequin.core_types import QueryResult
"""Render a query result deterministically in horizontal or vertical table form."""
def render_table(result: QueryResult) -> str: ...

"""Render catalog relations in deterministic table order."""
def render_catalog_relations(relations: CottList[CatalogRelation]) -> str: ...

"""Render catalog columns in deterministic table order."""
def render_catalog_columns(columns: CottList[CatalogColumn]) -> str: ...

"""Render catalog matches in deterministic table order."""
def render_catalog_matches(catalog_matches: CottList[CatalogMatch]) -> str: ...

__all__ = ["render_catalog_columns", "render_catalog_matches", "render_catalog_relations", "render_table"]
