from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.color_quantization_types import ColorQuantizationError as ColorQuantizationError, ColorQuantizationError_EmptyPixels as ColorQuantizationError_EmptyPixels, ColorQuantizationError_ZeroMaxColors as ColorQuantizationError_ZeroMaxColors, Palette as Palette, QuantizeRequest as QuantizeRequest, Rgb as Rgb
"""Count exact RGB values and return at most max_colors distinct colors,
ordered by descending frequency and then ascending red, green, and blue
components. Empty pixels or a zero limit produces an empty list."""
def rank_palette_colors(pixels: CottList[Rgb], max_colors: U8) -> CottList[Rgb]: ...

"""Reject an empty pixel collection before a zero color limit, then call
rank_palette_colors and construct the resulting palette."""
def quantize_colors(request: QuantizeRequest) -> Result[Palette, ColorQuantizationError]: ...

__all__ = ["ColorQuantizationError", "ColorQuantizationError_EmptyPixels", "ColorQuantizationError_ZeroMaxColors", "Palette", "QuantizeRequest", "Rgb", "quantize_colors", "rank_palette_colors"]
