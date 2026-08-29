from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from starlette.requests import Request as _cott_external_HttpRequest
HttpRequest: TypeAlias = Annotated[_cott_external_HttpRequest, CottExternal("starlette.requests:Request")]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HelloResponse:
    __hash__ = None
    message: str
    method: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "message", _cott_validate_abi(self.message, str, path="$.message"))
        if not _cott_validated_construction():
            object.__setattr__(self, "method", _cott_validate_abi(self.method, str, path="$.method"))

"""Return FastAPI's official `Hello World` message and the injected request method."""
__all__ = ["HelloResponse", "HttpRequest"]
