from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Get:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Head:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Post:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Put:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Patch:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Delete:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Options:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Custom:
    __hash__ = None
    name: str

HttpMethod: TypeAlias = Union[HttpMethod_Get, HttpMethod_Head, HttpMethod_Post, HttpMethod_Put, HttpMethod_Patch, HttpMethod_Delete, HttpMethod_Options, HttpMethod_Custom]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Header:
    __hash__ = None
    name: str
    value: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Request:
    __hash__ = None
    method: HttpMethod
    url: str
    headers: CottList[Header]
    body: str
    timeout_ms: U32

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "method", _cott_validate_abi(self.method, HttpMethod, path="$.method"))
        if not _cott_validated_construction():
            object.__setattr__(self, "url", _cott_validate_abi(self.url, str, path="$.url"))
        if not _cott_validated_construction():
            object.__setattr__(self, "headers", _cott_validate_abi(self.headers, CottList[Header], path="$.headers"))
        if not _cott_validated_construction():
            object.__setattr__(self, "body", _cott_validate_abi(self.body, str, path="$.body"))
        if not _cott_validated_construction():
            object.__setattr__(self, "timeout_ms", _cott_validate_abi(self.timeout_ms, U32, path="$.timeout_ms"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Response:
    __hash__ = None
    status: U16
    url: str
    headers: CottList[Header]
    body: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "status", _cott_validate_abi(self.status, U16, path="$.status"))
        if not _cott_validated_construction():
            object.__setattr__(self, "url", _cott_validate_abi(self.url, str, path="$.url"))
        if not _cott_validated_construction():
            object.__setattr__(self, "headers", _cott_validate_abi(self.headers, CottList[Header], path="$.headers"))
        if not _cott_validated_construction():
            object.__setattr__(self, "body", _cott_validate_abi(self.body, str, path="$.body"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_InvalidArguments:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_InvalidRequest:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_NetworkFailed:
    __hash__ = None
    message: str

PostingError: TypeAlias = Union[PostingError_InvalidArguments, PostingError_InvalidRequest, PostingError_NetworkFailed]

"""Accept standard HTTP methods case-insensitively; preserve other non-empty methods."""
"""Parse METHOD URL [BODY]; use a 30-second timeout and no headers."""
"""Send one HTTP request and retain status, final URL, headers, and response bytes."""
"""Render status and final URL, then headers and a UTF-8 replacement-decoded body."""
"""Parse arguments, send the request, and render its response."""
__all__ = ["Header", "HttpMethod", "HttpMethod_Custom", "HttpMethod_Delete", "HttpMethod_Get", "HttpMethod_Head", "HttpMethod_Options", "HttpMethod_Patch", "HttpMethod_Post", "HttpMethod_Put", "PostingError", "PostingError_InvalidArguments", "PostingError_InvalidRequest", "PostingError_NetworkFailed", "Request", "Response"]
