from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.archive_request_types import ArchivePlan as ArchivePlan, ArchiveRequest as ArchiveRequest, ArchiveRequestError as ArchiveRequestError, ArchiveRequestError_EmptySelection as ArchiveRequestError_EmptySelection, ArchiveRequestError_InvalidUrl as ArchiveRequestError_InvalidUrl, CaptureKind as CaptureKind, CaptureKind_Html as CaptureKind_Html, CaptureKind_Media as CaptureKind_Media
"""Parse an HTTP or HTTPS URL and return its deterministic canonical form.
The scheme and host are lowercased while user information, port, path,
query, and fragment are retained. Invalid or malformed URLs return
InvalidUrl."""
def canonicalize_archive_url(url: str) -> Result[str, ArchiveRequestError]: ...

"""Assemble an archive plan from a canonical URL and the requested capture
kinds. HTML precedes media when both kinds are selected."""
def compose_archive_plan(canonical_url: str, include_html: bool, include_media: bool) -> ArchivePlan: ...

"""Reject a request with neither capture kind selected as EmptySelection before
canonicalizing its URL. Otherwise canonicalize the URL and compose the plan;
malformed URLs return InvalidUrl."""
def plan_archive(request: ArchiveRequest) -> Result[ArchivePlan, ArchiveRequestError]: ...

__all__ = ["ArchivePlan", "ArchiveRequest", "ArchiveRequestError", "ArchiveRequestError_EmptySelection", "ArchiveRequestError_InvalidUrl", "CaptureKind", "CaptureKind_Html", "CaptureKind_Media", "canonicalize_archive_url", "compose_archive_plan", "plan_archive"]
