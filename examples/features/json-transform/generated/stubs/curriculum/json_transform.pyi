from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.json_transform_types import JsonChain as JsonChain, JsonChain_End as JsonChain_End, JsonChain_Link as JsonChain_Link, JsonTransformError as JsonTransformError, JsonTransformError_MissingField as JsonTransformError_MissingField, JsonTransformError_NotAnObject as JsonTransformError_NotAnObject, StringField as StringField
"""Wrap one string member into a JSON object."""
async def wrap_scalar_json(key: str, value: str) -> JsonValue: ...

"""Read the top-level member of a JSON object whose key equals `field` exactly
(no case folding, normalization or nested lookup). A payload that is not a
JSON object fails with `NotAnObject`, checked first. An object without that
member, or whose member is not a JSON string, fails with
`MissingField(field_name: field)`. Otherwise the result's `name` is `field`
and its `text` is the member's string value. Contract clauses cannot inspect
`JsonValue` structure, so both failures are declared without conditions."""
def extract_string_field(payload: JsonValue, field: str) -> Result[StringField, JsonTransformError]: ...

__all__ = ["JsonChain", "JsonChain_End", "JsonChain_Link", "JsonTransformError", "JsonTransformError_MissingField", "JsonTransformError_NotAnObject", "StringField", "extract_string_field", "wrap_scalar_json"]
