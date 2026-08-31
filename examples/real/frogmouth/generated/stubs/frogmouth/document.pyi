from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.document_types import LoadError as LoadError, LoadError_InvalidEncoding as LoadError_InvalidEncoding, LoadError_NetworkFailed as LoadError_NetworkFailed, LoadError_NotFound as LoadError_NotFound, LoadError_ReadFailed as LoadError_ReadFailed, LoadError_TooLarge as LoadError_TooLarge
from frogmouth.model_types import Document, Location
"""Load at most 5 MiB of UTF-8 Markdown and derive a title from its first heading."""
def load_document(location: Location) -> Result[Document, LoadError]: ...

__all__ = ["LoadError", "LoadError_InvalidEncoding", "LoadError_NetworkFailed", "LoadError_NotFound", "LoadError_ReadFailed", "LoadError_TooLarge", "load_document"]
