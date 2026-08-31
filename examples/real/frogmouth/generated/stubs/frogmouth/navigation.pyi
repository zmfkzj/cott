from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.navigation_types import NavigationError as NavigationError, NavigationError_EmptyInput as NavigationError_EmptyInput, NavigationError_UnsupportedScheme as NavigationError_UnsupportedScheme
from frogmouth.model_types import Location
"""Return LocationKind.Http for HTTP(S); otherwise return an absolute LocationKind.Local path."""
def resolve_location(value: str, working_directory: Path) -> Result[Location, NavigationError]: ...

def display_location(location: Location) -> str: ...

__all__ = ["NavigationError", "NavigationError_EmptyInput", "NavigationError_UnsupportedScheme", "display_location", "resolve_location"]
