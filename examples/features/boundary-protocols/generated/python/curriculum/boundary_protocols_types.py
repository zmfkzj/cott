from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from io import StringIO as _cott_external_TextBuffer
TextBuffer: TypeAlias = Annotated[_cott_external_TextBuffer, CottExternal("io:StringIO")]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HandleBundle:
    __hash__ = None
    handle: Opaque[Literal["client_session"]]
    raw_id: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "handle", _cott_validate_abi(self.handle, Opaque[Literal["client_session"]], path="$.handle"))
        if not _cott_validated_construction():
            object.__setattr__(self, "raw_id", _cott_validate_abi(self.raw_id, U64, path="$.raw_id"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HandleError_InvalidHandle:
    pass

HandleError: TypeAlias = Union[HandleError_InvalidHandle]

"""Wrap a nonzero connection ID in a client-session opaque handle."""
"""Explicitly adapt a client-session opaque handle to its Python ID."""
"""Deliberately adapt an unconstrained value to an explicitly narrowed boundary value."""
"""Lazily yield buffer lines without trailing line endings."""
"""Yield each value, discard sent unknown values, and return the yield count."""
"""Return the supplied async iterator."""
"""Return the supplied async generator."""
__all__ = ["HandleBundle", "HandleError", "HandleError_InvalidHandle", "TextBuffer"]
