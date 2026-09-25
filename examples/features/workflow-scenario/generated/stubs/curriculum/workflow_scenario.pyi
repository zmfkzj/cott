from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.workflow_scenario_types import CANCELLED_QUERY as CANCELLED_QUERY, CANCELLED_REQUEST_ID as CANCELLED_REQUEST_ID, DRAFT_TEXT as DRAFT_TEXT, FIRST_SAVE_REVISION as FIRST_SAVE_REVISION, LATEST_SAVE_REVISION as LATEST_SAVE_REVISION, NEW_QUERY as NEW_QUERY, NEW_REQUEST_ID as NEW_REQUEST_ID, NEW_RESULT as NEW_RESULT, OLD_QUERY as OLD_QUERY, OLD_REQUEST_ID as OLD_REQUEST_ID, PUBLISHED_TEXT as PUBLISHED_TEXT, SaveReceipt as SaveReceipt, SaveSnapshot as SaveSnapshot, SaveStatus as SaveStatus, SaveStatus_Flushed as SaveStatus_Flushed, SaveStatus_Queued as SaveStatus_Queued, SearchResult as SearchResult, SearchSnapshot as SearchSnapshot, SearchStatus as SearchStatus, SearchStatus_Loading as SearchStatus_Loading, SearchStatus_Ready as SearchStatus_Ready
"""Start the snapshot of a new search request. Nothing is applied yet, so the
snapshot is Loading with applied_request_id 0 and an empty result."""
def begin_search(request_id: U64, query: str) -> SearchSnapshot: ...

"""Resolve one search request without observing host state. This lesson's
resolver is a deterministic stand-in: the result text is the query followed
by " result", so query "new" resolves to "new result"."""
async def resolve_search(request_id: U64, query: str) -> SearchResult: ...

"""Apply a resolved result only when it belongs to the snapshot's request.
A matching candidate makes the snapshot Ready with the candidate's result;
a candidate for any other request is stale and leaves the snapshot
unchanged, so an older result can never overwrite a newer request."""
def apply_search(snapshot: SearchSnapshot, candidate: SearchResult) -> SearchSnapshot: ...

"""Queue the first save request for revision."""
def begin_save(revision: U64, text: str) -> SaveSnapshot: ...

"""Coalesce a save request into the pending snapshot. Only a strictly newer
revision replaces the pending request and queues it; an equal or older
revision is ignored and the snapshot is returned unchanged."""
def request_save(snapshot: SaveSnapshot, revision: U64, text: str) -> SaveSnapshot: ...

"""Flush the coalesced save request and return its Flushed receipt."""
def flush_save(snapshot: SaveSnapshot) -> SaveReceipt: ...

__all__ = ["CANCELLED_QUERY", "CANCELLED_REQUEST_ID", "DRAFT_TEXT", "FIRST_SAVE_REVISION", "LATEST_SAVE_REVISION", "NEW_QUERY", "NEW_REQUEST_ID", "NEW_RESULT", "OLD_QUERY", "OLD_REQUEST_ID", "PUBLISHED_TEXT", "SaveReceipt", "SaveSnapshot", "SaveStatus", "SaveStatus_Flushed", "SaveStatus_Queued", "SearchResult", "SearchSnapshot", "SearchStatus", "SearchStatus_Loading", "SearchStatus_Ready", "apply_search", "begin_save", "begin_search", "flush_save", "request_save", "resolve_search"]
