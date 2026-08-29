from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.navigation_types import NavigationError as NavigationError, NavigationError_EmptyInput as NavigationError_EmptyInput, NavigationError_InvalidLocation as NavigationError_InvalidLocation, NavigationError_MissingBase as NavigationError_MissingBase, NavigationError_UnsupportedScheme as NavigationError_UnsupportedScheme
from frogmouth.model_types import Location
def normalize_location_input(value: str) -> Result[str, NavigationError]: ...

def resolve_forge_location(value: str) -> Result[Location, NavigationError]: ...

def resolve_absolute_location(value: str) -> Result[Location, NavigationError]: ...

def resolve_relative_location(value: str, base: Option[Location], working_directory: Path) -> Result[Location, NavigationError]: ...

def resolve_location(value: str, base: Option[Location], working_directory: Path) -> Result[Location, NavigationError]: ...

"""Report whether location normalization succeeded."""
def normalization_is_ok(result: Result[str, NavigationError]) -> bool: ...

"""Report whether location resolution succeeded."""
def location_resolution_is_ok(result: Result[Location, NavigationError]) -> bool: ...

def display_location(location: Location) -> str: ...

__all__ = ["NavigationError", "NavigationError_EmptyInput", "NavigationError_InvalidLocation", "NavigationError_MissingBase", "NavigationError_UnsupportedScheme", "display_location", "location_resolution_is_ok", "normalization_is_ok", "normalize_location_input", "resolve_absolute_location", "resolve_forge_location", "resolve_location", "resolve_relative_location"]
