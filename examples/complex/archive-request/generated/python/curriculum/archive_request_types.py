from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CaptureKind_Html:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CaptureKind_Media:
    pass

CaptureKind: TypeAlias = Union[CaptureKind_Html, CaptureKind_Media]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ArchiveRequest:
    __hash__ = None
    url: str
    include_html: bool
    include_media: bool

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ArchivePlan:
    __hash__ = None
    canonical_url: str
    captures: CottList[CaptureKind]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ArchiveRequestError_InvalidUrl:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ArchiveRequestError_EmptySelection:
    pass

ArchiveRequestError: TypeAlias = Union[ArchiveRequestError_InvalidUrl, ArchiveRequestError_EmptySelection]

"""Parse an HTTP or HTTPS URL and return its deterministic canonical form.
The scheme and host are lowercased while user information, port, path,
query, and fragment are retained. Invalid or malformed URLs return
InvalidUrl."""
"""Assemble an archive plan from a canonical URL and the requested capture
kinds. HTML precedes media when both kinds are selected."""
"""Reject a request with neither capture kind selected as EmptySelection before
canonicalizing its URL. Otherwise canonicalize the URL and compose the plan;
malformed URLs return InvalidUrl."""
__all__ = ["ArchivePlan", "ArchiveRequest", "ArchiveRequestError", "ArchiveRequestError_EmptySelection", "ArchiveRequestError_InvalidUrl", "CaptureKind", "CaptureKind_Html", "CaptureKind_Media"]
