from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.document_types import LoadError as LoadError, LoadError_HttpFailure as LoadError_HttpFailure, LoadError_InvalidEncoding as LoadError_InvalidEncoding, LoadError_InvalidLocation as LoadError_InvalidLocation, LoadError_NetworkUnavailable as LoadError_NetworkUnavailable, LoadError_NotFound as LoadError_NotFound, LoadError_PermissionDenied as LoadError_PermissionDenied, LoadError_ReadFailure as LoadError_ReadFailure, LoadError_TooLarge as LoadError_TooLarge
from frogmouth.model_types import Document, Location
"""Remove YAML front matter from Markdown."""
def strip_front_matter(markdown: str) -> str: ...

def load_local_markdown(path: str) -> Result[str, LoadError]: ...

def load_http_markdown(url: str) -> Result[str, LoadError]: ...

"""Report whether Markdown loading succeeded."""
def markdown_result_is_ok(value: Result[str, LoadError]) -> bool: ...

def load_github_markdown(repository: str) -> Result[str, LoadError]: ...

def load_codeberg_markdown(repository: str) -> Result[str, LoadError]: ...

def location_title_fallback(location: Location) -> str: ...

def derive_document_title(markdown: str, fallback: str) -> str: ...

def load_document(location: Location) -> Result[Document, LoadError]: ...

__all__ = ["LoadError", "LoadError_HttpFailure", "LoadError_InvalidEncoding", "LoadError_InvalidLocation", "LoadError_NetworkUnavailable", "LoadError_NotFound", "LoadError_PermissionDenied", "LoadError_ReadFailure", "LoadError_TooLarge", "derive_document_title", "load_codeberg_markdown", "load_document", "load_github_markdown", "load_http_markdown", "load_local_markdown", "location_title_fallback", "markdown_result_is_ok", "strip_front_matter"]
