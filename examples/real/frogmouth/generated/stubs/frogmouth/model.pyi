from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.model_types import Document as Document, Location as Location, LocationKind as LocationKind, LocationKind_Http as LocationKind_Http, LocationKind_Local as LocationKind_Local
__all__ = ["Document", "Location", "LocationKind", "LocationKind_Http", "LocationKind_Local"]
