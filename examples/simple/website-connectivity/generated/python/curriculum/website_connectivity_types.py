from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottExternal, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class WebsiteObservation:
    __hash__ = None
    url: str
    status_code: I32

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectivityStatus_Working:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConnectivityStatus_NotWorking:
    pass

ConnectivityStatus: TypeAlias = Union[ConnectivityStatus_Working, ConnectivityStatus_NotWorking]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class WebsiteClassification:
    __hash__ = None
    url: str
    status: ConnectivityStatus

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class WebsiteObservationError_EmptyUrl:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class WebsiteObservationError_InvalidStatusCode:
    pass

WebsiteObservationError: TypeAlias = Union[WebsiteObservationError_EmptyUrl, WebsiteObservationError_InvalidStatusCode]

"""Validates and classifies one caller-supplied HTTP status observation.

An empty URL returns EmptyUrl before the status code is checked;
whitespace-only and otherwise nonempty URLs are accepted as opaque text
and preserved exactly. A status code outside the inclusive HTTP range 100
through 599 returns InvalidStatusCode.

Status 200 maps to Working; every other accepted status maps to NotWorking."""
"""Classifies website observations by applying classify_observation to each
item in input order.

The first invalid observation is returned unchanged. Within each item, an
empty URL takes priority over an invalid status code. Success contains one
classification per observation in the same order; empty input succeeds."""
__all__ = ["ConnectivityStatus", "ConnectivityStatus_NotWorking", "ConnectivityStatus_Working", "WebsiteClassification", "WebsiteObservation", "WebsiteObservationError", "WebsiteObservationError_EmptyUrl", "WebsiteObservationError_InvalidStatusCode"]
