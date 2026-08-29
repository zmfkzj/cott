from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaItem:
    __hash__ = None
    url: str
    id: str
    title: str
    ext: str
    playlist_index: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "url", _cott_validate_abi(self.url, str, path="$.url"))
        if not _cott_validated_construction():
            object.__setattr__(self, "id", _cott_validate_abi(self.id, str, path="$.id"))
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ext", _cott_validate_abi(self.ext, str, path="$.ext"))
        if not _cott_validated_construction():
            object.__setattr__(self, "playlist_index", _cott_validate_abi(self.playlist_index, U64, path="$.playlist_index"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PlaylistRange:
    __hash__ = None
    first: U64
    last: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "first", _cott_validate_abi(self.first, U64, path="$.first"))
        if not _cott_validated_construction():
            object.__setattr__(self, "last", _cott_validate_abi(self.last, U64, path="$.last"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DownloadPlan:
    __hash__ = None
    items: CottList[MediaItem]
    stopped_on_archive: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "items", _cott_validate_abi(self.items, CottList[MediaItem], path="$.items"))
        if not _cott_validated_construction():
            object.__setattr__(self, "stopped_on_archive", _cott_validate_abi(self.stopped_on_archive, bool, path="$.stopped_on_archive"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransferRequest:
    __hash__ = None
    url: str
    destination: Path
    simulate: bool
    max_bytes: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "url", _cott_validate_abi(self.url, str, path="$.url"))
        if not _cott_validated_construction():
            object.__setattr__(self, "destination", _cott_validate_abi(self.destination, Path, path="$.destination"))
        if not _cott_validated_construction():
            object.__setattr__(self, "simulate", _cott_validate_abi(self.simulate, bool, path="$.simulate"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_bytes", _cott_validate_abi(self.max_bytes, U64, path="$.max_bytes"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TransferReceipt:
    __hash__ = None
    url: str
    destination: Path
    bytes_written: U64
    simulated: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "url", _cott_validate_abi(self.url, str, path="$.url"))
        if not _cott_validated_construction():
            object.__setattr__(self, "destination", _cott_validate_abi(self.destination, Path, path="$.destination"))
        if not _cott_validated_construction():
            object.__setattr__(self, "bytes_written", _cott_validate_abi(self.bytes_written, U64, path="$.bytes_written"))
        if not _cott_validated_construction():
            object.__setattr__(self, "simulated", _cott_validate_abi(self.simulated, bool, path="$.simulated"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonMode_Lines:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class JsonMode_Single:
    pass

JsonMode: TypeAlias = Union[JsonMode_Lines, JsonMode_Single]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_InvalidInput:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_InvalidRange:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_InvalidTemplate:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_UnsupportedUrl:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_HttpStatus:
    __hash__ = None
    status: U16

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_NetworkFailure:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_OutputFailure:
    __hash__ = None
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MediaError_SizeLimit:
    pass

MediaError: TypeAlias = Union[MediaError_InvalidInput, MediaError_InvalidRange, MediaError_InvalidTemplate, MediaError_UnsupportedUrl, MediaError_HttpStatus, MediaError_NetworkFailure, MediaError_OutputFailure, MediaError_SizeLimit]

"""Parse trimmed batch URLs while ignoring configured comment prefixes."""
"""Expand one-based inclusive playlist ranges deterministically."""
"""Preserve item order while applying archive and break-on-existing policy."""
"""Substitute a bounded output template with a configurable missing value."""
"""Render items as compact JSON Lines or one compact JSON array."""
"""Simulate or atomically transfer one bounded direct HTTP(S) resource."""
__all__ = ["DownloadPlan", "JsonMode", "JsonMode_Lines", "JsonMode_Single", "MediaError", "MediaError_HttpStatus", "MediaError_InvalidInput", "MediaError_InvalidRange", "MediaError_InvalidTemplate", "MediaError_NetworkFailure", "MediaError_OutputFailure", "MediaError_SizeLimit", "MediaError_UnsupportedUrl", "MediaItem", "PlaylistRange", "TransferReceipt", "TransferRequest"]
