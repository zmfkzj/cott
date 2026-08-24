from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottExternal, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Rgb:
    __hash__ = None
    red: U8
    green: U8
    blue: U8

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class QuantizeRequest:
    __hash__ = None
    pixels: CottList[Rgb]
    max_colors: U8

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Palette:
    __hash__ = None
    colors: CottList[Rgb]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ColorQuantizationError_EmptyPixels:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ColorQuantizationError_ZeroMaxColors:
    pass

ColorQuantizationError: TypeAlias = Union[ColorQuantizationError_EmptyPixels, ColorQuantizationError_ZeroMaxColors]

"""Count exact RGB values and return at most max_colors distinct colors,
ordered by descending frequency and then ascending red, green, and blue
components. Empty pixels or a zero limit produces an empty list."""
"""Reject an empty pixel collection before a zero color limit, then call
rank_palette_colors and construct the resulting palette."""
__all__ = ["ColorQuantizationError", "ColorQuantizationError_EmptyPixels", "ColorQuantizationError_ZeroMaxColors", "Palette", "QuantizeRequest", "Rgb"]
