from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.system_effects_types import SystemError as SystemError, SystemError_AccessDenied as SystemError_AccessDenied, SystemError_PathNotFound as SystemError_PathNotFound
"""Validate and inspect a system file path target."""
def inspect_file_path(target: Path) -> Result[Path, SystemError]: ...

"""Format an environment variable value or use the fallback string."""
def format_env_variable(var_name: str, fallback: str) -> str: ...

__all__ = ["SystemError", "SystemError_AccessDenied", "SystemError_PathNotFound", "format_env_variable", "inspect_file_path"]
