from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TrackDraft:
    __hash__ = None
    title: str
    artist: str
    album: str
    track_no: U16

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TrackMetadata:
    __hash__ = None
    display: str
    sort_key: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TrackMetadataError_BlankTitle:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TrackMetadataError_BlankArtist:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TrackMetadataError_ZeroTrackNumber:
    pass

TrackMetadataError: TypeAlias = Union[TrackMetadataError_BlankTitle, TrackMetadataError_BlankArtist, TrackMetadataError_ZeroTrackNumber]

"""Removes leading and trailing Unicode whitespace from the title, artist,
and album while preserving the track number.

This total normalization step does not reject blank trimmed fields, so it
is safe to call independently for every TrackDraft."""
"""Formats one track draft as display and sorting metadata without validation.

The display is `artist — title`. The sort key contains the Unicode-
lowercased artist, Unicode-lowercased album, and decimal track number,
separated by U+0000. The track number is padded to at least four digits.
This total formatting step is safe for every TrackDraft."""
"""Validates, trims, and formats one track draft.

A zero track number is rejected before trimming. The draft is then
normalized by trim_track_draft. A blank trimmed title is rejected before a
blank trimmed artist. Successful normalized drafts are passed to
format_track_metadata."""
__all__ = ["TrackDraft", "TrackMetadata", "TrackMetadataError", "TrackMetadataError_BlankArtist", "TrackMetadataError_BlankTitle", "TrackMetadataError_ZeroTrackNumber"]
