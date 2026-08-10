from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.website_connectivity_types import ConnectivityStatus as ConnectivityStatus, ConnectivityStatus_NotWorking as ConnectivityStatus_NotWorking, ConnectivityStatus_Working as ConnectivityStatus_Working, WebsiteClassification as WebsiteClassification, WebsiteObservation as WebsiteObservation, WebsiteObservationError as WebsiteObservationError, WebsiteObservationError_EmptyUrl as WebsiteObservationError_EmptyUrl, WebsiteObservationError_InvalidStatusCode as WebsiteObservationError_InvalidStatusCode
"""Validates and classifies one caller-supplied HTTP status observation.

An empty URL returns EmptyUrl before the status code is checked;
whitespace-only and otherwise nonempty URLs are accepted as opaque text
and preserved exactly. A status code outside the inclusive HTTP range 100
through 599 returns InvalidStatusCode.

Status 200 maps to Working; every other accepted status maps to NotWorking."""
def classify_observation(observation: WebsiteObservation) -> Result[WebsiteClassification, WebsiteObservationError]: ...

"""Classifies website observations by applying classify_observation to each
item in input order.

The first invalid observation is returned unchanged. Within each item, an
empty URL takes priority over an invalid status code. Success contains one
classification per observation in the same order; empty input succeeds."""
def classify_websites(observations: CottList[WebsiteObservation]) -> Result[CottList[WebsiteClassification], WebsiteObservationError]: ...

__all__ = ["ConnectivityStatus", "ConnectivityStatus_NotWorking", "ConnectivityStatus_Working", "WebsiteClassification", "WebsiteObservation", "WebsiteObservationError", "WebsiteObservationError_EmptyUrl", "WebsiteObservationError_InvalidStatusCode", "classify_observation", "classify_websites"]
