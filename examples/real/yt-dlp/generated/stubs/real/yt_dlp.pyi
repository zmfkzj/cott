from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.yt_dlp_types import DownloadPlan as DownloadPlan, JsonMode as JsonMode, JsonMode_Lines as JsonMode_Lines, JsonMode_Single as JsonMode_Single, MediaError as MediaError, MediaError_HttpStatus as MediaError_HttpStatus, MediaError_InvalidInput as MediaError_InvalidInput, MediaError_InvalidRange as MediaError_InvalidRange, MediaError_InvalidTemplate as MediaError_InvalidTemplate, MediaError_NetworkFailure as MediaError_NetworkFailure, MediaError_OutputFailure as MediaError_OutputFailure, MediaError_SizeLimit as MediaError_SizeLimit, MediaError_UnsupportedUrl as MediaError_UnsupportedUrl, MediaItem as MediaItem, PlaylistRange as PlaylistRange, TransferReceipt as TransferReceipt, TransferRequest as TransferRequest
"""Parse trimmed batch URLs while ignoring configured comment prefixes."""
def parse_batch_urls(batch: str, comment_prefixes: CottList[str]) -> Result[CottList[str], MediaError]: ...

"""Expand one-based inclusive playlist ranges deterministically."""
def expand_playlist_ranges(items: CottList[MediaItem], ranges: CottList[PlaylistRange]) -> Result[CottList[MediaItem], MediaError]: ...

"""Preserve item order while applying archive and break-on-existing policy."""
def plan_downloads(items: CottList[MediaItem], archive: CottList[str], break_on_existing: bool) -> DownloadPlan: ...

"""Substitute a bounded output template with a configurable missing value."""
def render_output_path(item: MediaItem, template: str, missing_placeholder: str) -> Result[str, MediaError]: ...

"""Render items as compact JSON Lines or one compact JSON array."""
def render_items(items: CottList[MediaItem], mode: JsonMode) -> str: ...

"""Simulate or atomically transfer one bounded direct HTTP(S) resource."""
def transfer_media(request: TransferRequest) -> Result[TransferReceipt, MediaError]: ...

__all__ = ["DownloadPlan", "JsonMode", "JsonMode_Lines", "JsonMode_Single", "MediaError", "MediaError_HttpStatus", "MediaError_InvalidInput", "MediaError_InvalidRange", "MediaError_InvalidTemplate", "MediaError_NetworkFailure", "MediaError_OutputFailure", "MediaError_SizeLimit", "MediaError_UnsupportedUrl", "MediaItem", "PlaylistRange", "TransferReceipt", "TransferRequest", "expand_playlist_ranges", "parse_batch_urls", "plan_downloads", "render_items", "render_output_path", "transfer_media"]
