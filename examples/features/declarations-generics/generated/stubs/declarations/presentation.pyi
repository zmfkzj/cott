from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit
from declarations.core_types import ByteBlock, LABEL_BYTES, LabelFrame, NonEmptyLabel
"""Return a named fixed-width label, its covariant array-payload frame, and matching raw bytes."""
def package_label(label: NonEmptyLabel, values: CottArray[U8, Literal[4]], raw: CottBuffer[Literal[4]]) -> tuple[str, LabelFrame[CottArray[U8, Literal[4]]], ByteBlock[Literal[4]]]: ...

__all__ = ["package_label"]
