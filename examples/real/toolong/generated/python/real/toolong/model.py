from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.toolong.model_types import ByteSpan, Compression, Compression_Bzip2, Compression_Gzip, Compression_Uncompressed, FileIndex, FileTimestamps, FindQuery, LineFormat, LineFormat_CombinedLog, LineFormat_CommonLog, LineFormat_Json, LineFormat_Plain, LineLocation, LogSource, LogTimestamp, MergedIndex, MergedLine, ParsedLine, PipeFeed, Rect, ScreenRow, StyledRun, StyledSpan, StyledText, TabIndex, TabIndex_Merged, TabIndex_Single, TabPlan, TermColor, TermColor_Default, TermColor_Indexed, TermColor_Rgb, TimeUnit, TimeUnit_Day, TimeUnit_Hour, TimeUnit_Minute, TimestampEntry, TimestampScan, ViewerSetup

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

__all__ = ["ByteSpan", "Compression", "Compression_Bzip2", "Compression_Gzip", "Compression_Uncompressed", "FileIndex", "FileTimestamps", "FindQuery", "LineFormat", "LineFormat_CombinedLog", "LineFormat_CommonLog", "LineFormat_Json", "LineFormat_Plain", "LineLocation", "LogSource", "LogTimestamp", "MergedIndex", "MergedLine", "ParsedLine", "PipeFeed", "Rect", "ScreenRow", "StyledRun", "StyledSpan", "StyledText", "TabIndex", "TabIndex_Merged", "TabIndex_Single", "TabPlan", "TermColor", "TermColor_Default", "TermColor_Indexed", "TermColor_Rgb", "TimeUnit", "TimeUnit_Day", "TimeUnit_Hour", "TimeUnit_Minute", "TimestampEntry", "TimestampScan", "ViewerSetup"]
