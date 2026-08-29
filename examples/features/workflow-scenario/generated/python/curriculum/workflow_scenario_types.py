from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SearchStatus_Loading:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SearchStatus_Ready:
    pass

SearchStatus: TypeAlias = Union[SearchStatus_Loading, SearchStatus_Ready]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SearchSnapshot:
    __hash__ = None
    request_id: U64
    applied_request_id: U64
    query: str
    result: str
    status: SearchStatus

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "request_id", _cott_validate_abi(self.request_id, U64, path="$.request_id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "applied_request_id", _cott_validate_abi(self.applied_request_id, U64, path="$.applied_request_id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "query", _cott_validate_abi(self.query, str, path="$.query"))
        if not _cott_validated_construction():
            object.__setattr__(self, "result", _cott_validate_abi(self.result, str, path="$.result"))
        if not _cott_validated_construction():
            object.__setattr__(self, "status", _cott_validate_abi(self.status, SearchStatus, path="$.status"))
        if not (((self).request_id > 0)):
            raise CottContractViolation("invariant failed", symbol="curriculum.workflow_scenario.SearchSnapshot", clause="invariant:0", phase="invariant", span={"end_byte":240,"end_column":34,"end_line":14,"start_byte":211,"start_column":5,"start_line":14}, expected="true", actual="false")
        if not (((self).applied_request_id <= (self).request_id)):
            raise CottContractViolation("invariant failed", symbol="curriculum.workflow_scenario.SearchSnapshot", clause="invariant:1", phase="invariant", span={"end_byte":297,"end_column":57,"end_line":15,"start_byte":245,"start_column":5,"start_line":15}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SearchResult:
    __hash__ = None
    request_id: U64
    query: str
    result: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "request_id", _cott_validate_abi(self.request_id, U64, path="$.request_id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "query", _cott_validate_abi(self.query, str, path="$.query"))
        if not _cott_validated_construction():
            object.__setattr__(self, "result", _cott_validate_abi(self.result, str, path="$.result"))
        if not (((self).request_id > 0)):
            raise CottContractViolation("invariant failed", symbol="curriculum.workflow_scenario.SearchResult", clause="invariant:0", phase="invariant", span={"end_byte":405,"end_column":34,"end_line":22,"start_byte":376,"start_column":5,"start_line":22}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SaveStatus_Queued:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SaveStatus_Flushed:
    pass

SaveStatus: TypeAlias = Union[SaveStatus_Queued, SaveStatus_Flushed]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SaveSnapshot:
    __hash__ = None
    revision: U64
    text: str
    status: SaveStatus

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "revision", _cott_validate_abi(self.revision, U64, path="$.revision"))
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "status", _cott_validate_abi(self.status, SaveStatus, path="$.status"))
        if not (((self).revision > 0)):
            raise CottContractViolation("invariant failed", symbol="curriculum.workflow_scenario.SaveSnapshot", clause="invariant:0", phase="invariant", span={"end_byte":556,"end_column":32,"end_line":33,"start_byte":529,"start_column":5,"start_line":33}, expected="true", actual="false")

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SaveReceipt:
    __hash__ = None
    revision: U64
    text: str
    status: SaveStatus

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "revision", _cott_validate_abi(self.revision, U64, path="$.revision"))
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "status", _cott_validate_abi(self.status, SaveStatus, path="$.status"))
        if not (((self).revision > 0)):
            raise CottContractViolation("invariant failed", symbol="curriculum.workflow_scenario.SaveReceipt", clause="invariant:0", phase="invariant", span={"end_byte":665,"end_column":32,"end_line":40,"start_byte":638,"start_column":5,"start_line":40}, expected="true", actual="false")

"""Start an immutable public search snapshot for the supplied request."""
"""Resolve one immutable search result without observing host state."""
"""Apply a result only when it still belongs to the snapshot's newest request."""
"""Queue the first immutable save request."""
"""Coalesce a newer save request into the public queued snapshot."""
"""Return the public receipt for the currently coalesced save request."""
OLD_REQUEST_ID: Final[U64] = 1

NEW_REQUEST_ID: Final[U64] = 2

CANCELLED_REQUEST_ID: Final[U64] = 3

FIRST_SAVE_REVISION: Final[U64] = 1

LATEST_SAVE_REVISION: Final[U64] = 2

OLD_QUERY: Final[str] = "old"

NEW_QUERY: Final[str] = "new"

CANCELLED_QUERY: Final[str] = "cancelled"

DRAFT_TEXT: Final[str] = "draft"

PUBLISHED_TEXT: Final[str] = "published"

NEW_RESULT: Final[str] = "new result"

__all__ = ["CANCELLED_QUERY", "CANCELLED_REQUEST_ID", "DRAFT_TEXT", "FIRST_SAVE_REVISION", "LATEST_SAVE_REVISION", "NEW_QUERY", "NEW_REQUEST_ID", "NEW_RESULT", "OLD_QUERY", "OLD_REQUEST_ID", "PUBLISHED_TEXT", "SaveReceipt", "SaveSnapshot", "SaveStatus", "SaveStatus_Flushed", "SaveStatus_Queued", "SearchResult", "SearchSnapshot", "SearchStatus", "SearchStatus_Loading", "SearchStatus_Ready"]
