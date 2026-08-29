from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.persistence_types import StateError as StateError, StateError_InvalidData as StateError_InvalidData, StateError_IoFailure as StateError_IoFailure, StateError_PermissionDenied as StateError_PermissionDenied
from frogmouth.model_types import BrowserState, StateAction
def add_history(history: CottList[str], location: str, history_limit: U64) -> CottList[str]: ...

def toggle_bookmark(bookmarks: CottList[str], location: str) -> CottList[str]: ...

def remove_history(history: CottList[str], location: str) -> CottList[str]: ...

def decode_state(source: str, path: Path) -> Result[BrowserState, StateError]: ...

def encode_state(current: BrowserState) -> str: ...

def update_state(current: BrowserState, action: StateAction, history_limit: U64) -> BrowserState: ...

def load_state(path: Path) -> Result[BrowserState, StateError]: ...

def save_state(path: Path, current: BrowserState) -> Result[Unit, StateError]: ...

__all__ = ["StateError", "StateError_InvalidData", "StateError_IoFailure", "StateError_PermissionDenied", "add_history", "decode_state", "encode_state", "load_state", "remove_history", "save_state", "toggle_bookmark", "update_state"]
