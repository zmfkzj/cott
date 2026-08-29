from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.model_types import BrowserState as BrowserState, Document as Document, Location as Location, LocationKind as LocationKind, LocationKind_Codeberg as LocationKind_Codeberg, LocationKind_GitHub as LocationKind_GitHub, LocationKind_Local as LocationKind_Local, LocationKind_Remote as LocationKind_Remote, StateAction as StateAction, StateAction_AddHistory as StateAction_AddHistory, StateAction_ClearHistory as StateAction_ClearHistory, StateAction_RemoveHistory as StateAction_RemoveHistory, StateAction_ToggleBookmark as StateAction_ToggleBookmark
__all__ = ["BrowserState", "Document", "Location", "LocationKind", "LocationKind_Codeberg", "LocationKind_GitHub", "LocationKind_Local", "LocationKind_Remote", "StateAction", "StateAction_AddHistory", "StateAction_ClearHistory", "StateAction_RemoveHistory", "StateAction_ToggleBookmark"]
