from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
from io import StringIO as _cott_external_TextBuffer
TextBuffer: TypeAlias = Annotated[_cott_external_TextBuffer, CottExternal("io:StringIO")]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HandleBundle:
    __hash__ = None
    handle: Opaque[Literal["client_session"]]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HandleError_InvalidHandle:
    pass

HandleError: TypeAlias = Union[HandleError_InvalidHandle]

"""Wrap a nonzero connection ID in a bundle containing a client-session handle."""
"""Extract the client-session handle ID from a bundle returned by wrap_handle."""
"""Lazily yield the buffer's lines without their trailing line endings."""
"""Yield each input value, ignore sent values, and return the yielded count."""
__all__ = ["HandleBundle", "HandleError", "HandleError_InvalidHandle", "TextBuffer"]
