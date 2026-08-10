from __future__ import annotations

import dataclasses as _dataclasses
from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi

from curriculum.track_metadata_types import TrackDraft, TrackMetadata, TrackMetadataError, TrackMetadataError_BlankArtist, TrackMetadataError_BlankTitle, TrackMetadataError_ZeroTrackNumber

def trim_track_draft(draft: TrackDraft) -> TrackDraft:
    """Removes leading and trailing Unicode whitespace from the title, artist,
and album while preserving the track number.

This total normalization step does not reject blank trimmed fields, so it
is safe to call independently for every TrackDraft."""
    draft = _cott_validate_abi(draft, TrackDraft, path="$.draft")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/track_metadata/trim_track_draft.py", "916c5aa09c8bff9e66935aaea76b4d0d682f4ab3f9df1ddecd48089c9839975d", "trim_track_draft", expected_project_name="track-metadata", expected_cott_symbol="curriculum.track_metadata.trim_track_draft")
        _result = _implementation(draft)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.track_metadata.trim_track_draft"
        if _error.span is None:
            _error.span = {"end_byte":608,"end_column":1,"end_line":29,"start_byte":253,"start_column":1,"start_line":18}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.track_metadata.trim_track_draft", phase="implementation-call", span={"end_byte":608,"end_column":1,"end_line":29,"start_byte":253,"start_column":1,"start_line":18}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.track_metadata.trim_track_draft", phase="implementation-call", span={"end_byte":608,"end_column":1,"end_line":29,"start_byte":253,"start_column":1,"start_line":18}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, TrackDraft, path="$.return")
    return _result

def format_track_metadata(draft: TrackDraft) -> TrackMetadata:
    """Formats one track draft as display and sorting metadata without validation.

The display is `artist — title`. The sort key contains the Unicode-
lowercased artist, Unicode-lowercased album, and decimal track number,
separated by U+0000. The track number is padded to at least four digits.
This total formatting step is safe for every TrackDraft."""
    draft = _cott_validate_abi(draft, TrackDraft, path="$.draft")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/track_metadata/format_track_metadata.py", "e4e342fb4ff1143d5067ec0e8e4f87016ed861228c8fc70856c5daa98b43f24c", "format_track_metadata", expected_project_name="track-metadata", expected_cott_symbol="curriculum.track_metadata.format_track_metadata")
        _result = _implementation(draft)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.track_metadata.format_track_metadata"
        if _error.span is None:
            _error.span = {"end_byte":1079,"end_column":1,"end_line":41,"start_byte":608,"start_column":1,"start_line":29}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.track_metadata.format_track_metadata", phase="implementation-call", span={"end_byte":1079,"end_column":1,"end_line":41,"start_byte":608,"start_column":1,"start_line":29}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.track_metadata.format_track_metadata", phase="implementation-call", span={"end_byte":1079,"end_column":1,"end_line":41,"start_byte":608,"start_column":1,"start_line":29}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, TrackMetadata, path="$.return")
    return _result

def normalize_track_metadata(draft: TrackDraft) -> Result[TrackMetadata, TrackMetadataError]:
    """Validates, trims, and formats one track draft.

A zero track number is rejected before trimming. The draft is then
normalized by trim_track_draft. A blank trimmed title is rejected before a
blank trimmed artist. Successful normalized drafts are passed to
format_track_metadata."""
    draft = _cott_validate_abi(draft, TrackDraft, path="$.draft")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and (((draft).track_no == 0)):
        _expected_error = TrackMetadataError_ZeroTrackNumber
        _expected_error_span = {"end_byte":1625,"end_column":70,"end_line":53,"start_byte":1560,"start_column":5,"start_line":53}
        _expected_error_clause = "error:2"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/track_metadata/normalize_track_metadata.py", "9d49f3f5afdf1ca55dc12ded442cf93570d61d3561b01dc30482557ad4ecb245", "normalize_track_metadata", expected_project_name="track-metadata", expected_cott_symbol="curriculum.track_metadata.normalize_track_metadata")
        _result = _implementation(draft)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.track_metadata.normalize_track_metadata"
        if _error.span is None:
            _error.span = {"end_byte":1723,"end_column":1,"end_line":58,"start_byte":1079,"start_column":1,"start_line":41}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.track_metadata.normalize_track_metadata", phase="implementation-call", span={"end_byte":1723,"end_column":1,"end_line":58,"start_byte":1079,"start_column":1,"start_line":41}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.track_metadata.normalize_track_metadata", phase="implementation-call", span={"end_byte":1723,"end_column":1,"end_line":58,"start_byte":1079,"start_column":1,"start_line":41}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[TrackMetadata, TrackMetadataError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.track_metadata.normalize_track_metadata", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (TrackMetadataError_BlankTitle, TrackMetadataError_BlankArtist,):
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.track_metadata.normalize_track_metadata", phase="error", span={"end_byte":1723,"end_column":1,"end_line":58,"start_byte":1079,"start_column":1,"start_line":41}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.track_metadata.normalize_track_metadata", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if type(_result) is Ok and True:
        metadata = _result.value
        if not ((len((metadata).display) > 3)):
            raise CottContractViolation("ensures clause failed", symbol="curriculum.track_metadata.normalize_track_metadata", clause="ensures:1", phase="ensures", span={"end_byte":1554,"end_column":60,"end_line":51,"start_byte":1499,"start_column":5,"start_line":51}, expected="true", actual="false")
    return _result

__all__ = ["TrackDraft", "TrackMetadata", "TrackMetadataError", "TrackMetadataError_BlankArtist", "TrackMetadataError_BlankTitle", "TrackMetadataError_ZeroTrackNumber", "format_track_metadata", "normalize_track_metadata", "trim_track_draft"]
