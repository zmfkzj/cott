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
class HttpMethod_Head:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpMethod_Options:
    pass

HttpMethod: TypeAlias = Union[HttpMethod_Get, HttpMethod_Post, HttpMethod_Put, HttpMethod_Patch, HttpMethod_Delete, HttpMethod_Head, HttpMethod_Options]

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
class RequestDocument:
    __hash__ = None
    name: str
    method: HttpMethod
    url: str
    headers: CottList[Header]
    body: str
    json_body: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "method", _cott_validate_abi(self.method, HttpMethod, path="$.method"))
        if not _cott_validated_construction():
            object.__setattr__(self, "url", _cott_validate_abi(self.url, str, path="$.url"))
        if not _cott_validated_construction():
            object.__setattr__(self, "headers", _cott_validate_abi(self.headers, CottList[Header], path="$.headers"))
        if not _cott_validated_construction():
            object.__setattr__(self, "body", _cott_validate_abi(self.body, str, path="$.body"))
        if not _cott_validated_construction():
            object.__setattr__(self, "json_body", _cott_validate_abi(self.json_body, bool, path="$.json_body"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CollectionEntry:
    __hash__ = None
    path: Path
    name: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, Path, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HttpResponse:
    __hash__ = None
    status: U16
    headers: CottList[Header]
    body: bytes

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "status", _cott_validate_abi(self.status, U16, path="$.status"))
        if not _cott_validated_construction():
            object.__setattr__(self, "headers", _cott_validate_abi(self.headers, CottList[Header], path="$.headers"))
        if not _cott_validated_construction():
            object.__setattr__(self, "body", _cott_validate_abi(self.body, bytes, path="$.body"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_CollectionRootMissing:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_RequestMissing:
    __hash__ = None
    path: Path

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_InvalidYaml:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_InvalidRequest:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_InvalidHeader:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_InvalidJson:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_UnresolvedVariable:
    __hash__ = None
    name: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_NetworkFailed:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_TimedOut:
    __hash__ = None
    timeout_ms: U32

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_SaveFailed:
    __hash__ = None
    path: Path
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PostingError_ReadFailed:
    __hash__ = None
    path: Path
    message: str

PostingError: TypeAlias = Union[PostingError_CollectionRootMissing, PostingError_RequestMissing, PostingError_InvalidYaml, PostingError_InvalidRequest, PostingError_InvalidHeader, PostingError_InvalidJson, PostingError_UnresolvedVariable, PostingError_NetworkFailed, PostingError_TimedOut, PostingError_SaveFailed, PostingError_ReadFailed]

__all__ = ["CollectionEntry", "Header", "HttpMethod", "HttpMethod_Delete", "HttpMethod_Get", "HttpMethod_Head", "HttpMethod_Options", "HttpMethod_Patch", "HttpMethod_Post", "HttpMethod_Put", "HttpResponse", "PostingError", "PostingError_CollectionRootMissing", "PostingError_InvalidHeader", "PostingError_InvalidJson", "PostingError_InvalidRequest", "PostingError_InvalidYaml", "PostingError_NetworkFailed", "PostingError_ReadFailed", "PostingError_RequestMissing", "PostingError_SaveFailed", "PostingError_TimedOut", "PostingError_UnresolvedVariable", "RequestDocument"]
