from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.navigation_types import NavigationError as NavigationError, NavigationError_EmptyInput as NavigationError_EmptyInput, NavigationError_UnsupportedScheme as NavigationError_UnsupportedScheme
from frogmouth.model_types import Location, LocationKind, LocationKind_Http, LocationKind_Local
"""Classify address-bar input exactly as typed; it is not trimmed. A value
starting with "http://" or "https://" is an Http location whose target is the
value. Any other value containing "://" is UnsupportedScheme whose scheme is
the text before the first "://". Every other non-empty value is a Local
location: a value starting with "/" is the target unchanged; otherwise the
target is the text of working_directory, one "/" (omitted when that text
already ends with "/") and the value. Local targets are not normalized,
"~"-expanded or checked for existence. The browser passes the process's
absolute working directory."""
def resolve_location(value: str, working_directory: Path) -> Result[Location, NavigationError]: ...

"""Address-bar text for a loaded location; reload passes it back to
frogmouth.navigation.resolve_location."""
def display_location(location: Location) -> str: ...

__all__ = ["NavigationError", "NavigationError_EmptyInput", "NavigationError_UnsupportedScheme", "display_location", "resolve_location"]
