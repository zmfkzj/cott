from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottArray, CottBuffer, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.track_metadata_types import TrackDraft as TrackDraft, TrackMetadata as TrackMetadata, TrackMetadataError as TrackMetadataError, TrackMetadataError_BlankArtist as TrackMetadataError_BlankArtist, TrackMetadataError_BlankTitle as TrackMetadataError_BlankTitle, TrackMetadataError_ZeroTrackNumber as TrackMetadataError_ZeroTrackNumber
"""Removes leading and trailing Unicode whitespace from the title, artist,
and album while preserving the track number.

This total normalization step does not reject blank trimmed fields, so it
is safe to call independently for every TrackDraft."""
def trim_track_draft(draft: TrackDraft) -> TrackDraft: ...

"""Formats one track draft as display and sorting metadata without validation.

The display is `artist — title`. The sort key contains the Unicode-
lowercased artist, Unicode-lowercased album, and decimal track number,
separated by U+0000. The track number is padded to at least four digits.
This total formatting step is safe for every TrackDraft."""
def format_track_metadata(draft: TrackDraft) -> TrackMetadata: ...

"""Validates, trims, and formats one track draft.

A zero track number is rejected before trimming. The draft is then
normalized by trim_track_draft. A blank trimmed title is rejected before a
blank trimmed artist. Successful normalized drafts are passed to
format_track_metadata."""
def normalize_track_metadata(draft: TrackDraft) -> Result[TrackMetadata, TrackMetadataError]: ...

__all__ = ["TrackDraft", "TrackMetadata", "TrackMetadataError", "TrackMetadataError_BlankArtist", "TrackMetadataError_BlankTitle", "TrackMetadataError_ZeroTrackNumber", "format_track_metadata", "normalize_track_metadata", "trim_track_draft"]
