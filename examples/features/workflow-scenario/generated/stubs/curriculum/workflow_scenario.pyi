from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.workflow_scenario_types import CANCELLED_QUERY as CANCELLED_QUERY, CANCELLED_REQUEST_ID as CANCELLED_REQUEST_ID, DRAFT_TEXT as DRAFT_TEXT, FIRST_SAVE_REVISION as FIRST_SAVE_REVISION, LATEST_SAVE_REVISION as LATEST_SAVE_REVISION, NEW_QUERY as NEW_QUERY, NEW_REQUEST_ID as NEW_REQUEST_ID, NEW_RESULT as NEW_RESULT, OLD_QUERY as OLD_QUERY, OLD_REQUEST_ID as OLD_REQUEST_ID, PUBLISHED_TEXT as PUBLISHED_TEXT, SaveReceipt as SaveReceipt, SaveSnapshot as SaveSnapshot, SaveStatus as SaveStatus, SaveStatus_Flushed as SaveStatus_Flushed, SaveStatus_Queued as SaveStatus_Queued, SearchResult as SearchResult, SearchSnapshot as SearchSnapshot, SearchStatus as SearchStatus, SearchStatus_Loading as SearchStatus_Loading, SearchStatus_Ready as SearchStatus_Ready
"""Start an immutable public search snapshot for the supplied request."""
def begin_search(request_id: U64, query: str) -> SearchSnapshot: ...

"""Resolve one immutable search result without observing host state."""
async def resolve_search(request_id: U64, query: str) -> SearchResult: ...

"""Apply a result only when it still belongs to the snapshot's newest request."""
def apply_search(snapshot: SearchSnapshot, candidate: SearchResult) -> SearchSnapshot: ...

"""Queue the first immutable save request."""
def begin_save(revision: U64, text: str) -> SaveSnapshot: ...

"""Coalesce a newer save request into the public queued snapshot."""
def request_save(snapshot: SaveSnapshot, revision: U64, text: str) -> SaveSnapshot: ...

"""Return the public receipt for the currently coalesced save request."""
def flush_save(snapshot: SaveSnapshot) -> SaveReceipt: ...

__all__ = ["CANCELLED_QUERY", "CANCELLED_REQUEST_ID", "DRAFT_TEXT", "FIRST_SAVE_REVISION", "LATEST_SAVE_REVISION", "NEW_QUERY", "NEW_REQUEST_ID", "NEW_RESULT", "OLD_QUERY", "OLD_REQUEST_ID", "PUBLISHED_TEXT", "SaveReceipt", "SaveSnapshot", "SaveStatus", "SaveStatus_Flushed", "SaveStatus_Queued", "SearchResult", "SearchSnapshot", "SearchStatus", "SearchStatus_Loading", "SearchStatus_Ready", "apply_search", "begin_save", "begin_search", "flush_save", "request_save", "resolve_search"]
