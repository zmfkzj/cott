from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.json_transform_types import JsonTransformError as JsonTransformError, JsonTransformError_MissingField as JsonTransformError_MissingField, JsonTransformError_NotAnObject as JsonTransformError_NotAnObject
"""Wrap a string key-value pair into a structured JsonValue object."""
def wrap_scalar_json(key: str, value: str) -> JsonValue: ...

"""Extract a string field value from a JSON object payload."""
def extract_string_field(payload: JsonValue, field: str) -> Result[str, JsonTransformError]: ...

__all__ = ["JsonTransformError", "JsonTransformError_MissingField", "JsonTransformError_NotAnObject", "extract_string_field", "wrap_scalar_json"]
