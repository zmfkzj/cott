from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from io import StringIO as _cott_external_TextBuffer
TextBuffer: TypeAlias = Annotated[_cott_external_TextBuffer, CottExternal("io:StringIO")]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectionId:
    value: U64

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _cott_validate_abi(self.value, U64, path="$.value"))
        if not (_cott_contract_condition(((self.value > 0)), "curriculum.boundary_protocols.ConnectionId", "refinement")):
            raise CottContractViolation("ConnectionId refinement failed", symbol="curriculum.boundary_protocols.ConnectionId", phase="refinement", span={"end_byte":108,"end_column":19,"end_line":6,"start_byte":100,"start_column":11,"start_line":6}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class HandleBundle:
    __hash__ = None
    handle: Opaque[Literal["client_session"]]
    raw_id: ConnectionId

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "handle", _cott_validate_abi(self.handle, Opaque[Literal["client_session"]], path="$.handle"))
        if not _cott_validated_construction():
            object.__setattr__(self, "raw_id", _cott_validate_abi(self.raw_id, ConnectionId, path="$.raw_id"))

"""Wrap a connection ID in a client-session opaque handle.

The handle's opaque payload is the U64 value carried by `raw_id`, not the `ConnectionId`
wrapper and not a target object derived from it. `HandleBundle.raw_id` repeats the same ID
as plain data."""
"""Explicitly adapt a client-session opaque handle back to its connection ID by reading the
handle's opaque payload. `bundle` comes from `wrap_handle`; a handle carrying any other
payload is outside this contract."""
"""Retype an unconstrained `Any` value as `Unknown`, so that callers must narrow it explicitly
before use."""
"""Iterate the lines of a caller-owned text buffer. A line ends at LF, CR or CRLF, and the
terminator is not part of the yielded line. A final line without a terminator is still
yielded; an empty buffer yields nothing."""
"""Re-yield the values of an iterator from a generator. Values sent into the generator are
ignored; its return value is the number of values it yielded."""
"""Pass an async line iterator across the boundary."""
"""Pass an async generator across the boundary."""
__all__ = ["ConnectionId", "HandleBundle", "TextBuffer"]
