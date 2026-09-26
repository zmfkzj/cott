from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from frogmouth.branding_types import ABOUT_MESSAGE, ABOUT_TITLE, ADDRESS_PLACEHOLDER, APPLICATION_TITLE, BOOKMARK_TITLE_PROMPT, CLEAR_HISTORY_QUESTION, CLEAR_HISTORY_TITLE, DELETE_BOOKMARK_QUESTION, DELETE_BOOKMARK_TITLE, DELETE_HISTORY_QUESTION, DELETE_HISTORY_TITLE, DISCORD_URL, HELP_MARKDOWN, ORGANISATION_NAME, PACKAGE_NAME, PLACEHOLDER_MARKDOWN, USER_AGENT, VERSION

__all__ = ["ABOUT_MESSAGE", "ABOUT_TITLE", "ADDRESS_PLACEHOLDER", "APPLICATION_TITLE", "BOOKMARK_TITLE_PROMPT", "CLEAR_HISTORY_QUESTION", "CLEAR_HISTORY_TITLE", "DELETE_BOOKMARK_QUESTION", "DELETE_BOOKMARK_TITLE", "DELETE_HISTORY_QUESTION", "DELETE_HISTORY_TITLE", "DISCORD_URL", "HELP_MARKDOWN", "ORGANISATION_NAME", "PACKAGE_NAME", "PLACEHOLDER_MARKDOWN", "USER_AGENT", "VERSION"]
