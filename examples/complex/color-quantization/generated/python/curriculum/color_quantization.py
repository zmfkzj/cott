from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from curriculum.color_quantization_types import ColorQuantizationError, ColorQuantizationError_EmptyPixels, ColorQuantizationError_ZeroMaxColors, Palette, QuantizeRequest, Rgb

def rank_palette_colors(pixels: CottList[Rgb], max_colors: U8) -> CottList[Rgb]:
    """Count exact RGB values and return at most max_colors distinct colors,
ordered by descending frequency and then ascending red, green, and blue
components. Empty pixels or a zero limit produces an empty list."""
    pixels = _cott_validate_abi(pixels, CottList[Rgb], path="$.pixels")
    max_colors = _cott_validate_abi(max_colors, U8, path="$.max_colors")
    try:
        _implementation = _cott_load("_cott_impl/curriculum/color_quantization/rank_palette_colors.py", "5b157300bd1142781933af313355bd44cf198b91f7d50cb603efaa9ee427660e", "rank_palette_colors", expected_project_name="color-quantization", expected_cott_symbol="curriculum.color_quantization.rank_palette_colors")
        _result = _implementation(pixels, max_colors)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.color_quantization.rank_palette_colors"
        if _error.span is None:
            _error.span = {"end_byte":625,"end_column":1,"end_line":30,"start_byte":259,"start_column":1,"start_line":19}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.color_quantization.rank_palette_colors", phase="implementation-call", span={"end_byte":625,"end_column":1,"end_line":30,"start_byte":259,"start_column":1,"start_line":19}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.color_quantization.rank_palette_colors", phase="implementation-call", span={"end_byte":625,"end_column":1,"end_line":30,"start_byte":259,"start_column":1,"start_line":19}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CottList[Rgb], path="$.return")
    if not ((len(_result) <= len(pixels))):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.color_quantization.rank_palette_colors", clause="ensures:1", phase="ensures", span={"end_byte":607,"end_column":37,"end_line":26,"start_byte":575,"start_column":5,"start_line":26}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[Rgb], path="$.return", validator=_cott_validate_abi)
    return _result

def quantize_colors(request: QuantizeRequest) -> Result[Palette, ColorQuantizationError]:
    """Reject an empty pixel collection before a zero color limit, then call
rank_palette_colors and construct the resulting palette."""
    request = _cott_validate_abi(request, QuantizeRequest, path="$.request")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((request).pixels) == 0)):
        _expected_error = ColorQuantizationError_EmptyPixels
        _expected_error_span = {"end_byte":1001,"end_column":74,"end_line":38,"start_byte":932,"start_column":5,"start_line":38}
        _expected_error_clause = "error:2"
    if _expected_error is None and (((request).max_colors == 0)):
        _expected_error = ColorQuantizationError_ZeroMaxColors
        _expected_error_span = {"end_byte":1077,"end_column":76,"end_line":39,"start_byte":1006,"start_column":5,"start_line":39}
        _expected_error_clause = "error:3"
    try:
        _implementation = _cott_load("_cott_impl/curriculum/color_quantization/quantize_colors.py", "8a461900545c4396e2fee2cf1553ca8edf1da42da208b4d45ee10d726592d52f", "quantize_colors", expected_project_name="color-quantization", expected_cott_symbol="curriculum.color_quantization.quantize_colors")
        _result = _implementation(request)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "curriculum.color_quantization.quantize_colors"
        if _error.span is None:
            _error.span = {"end_byte":1094,"end_column":1,"end_line":42,"start_byte":625,"start_column":1,"start_line":30}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="curriculum.color_quantization.quantize_colors", phase="implementation-call", span={"end_byte":1094,"end_column":1,"end_line":42,"start_byte":625,"start_column":1,"start_line":30}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="curriculum.color_quantization.quantize_colors", phase="implementation-call", span={"end_byte":1094,"end_column":1,"end_line":42,"start_byte":625,"start_column":1,"start_line":30}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[Palette, ColorQuantizationError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="curriculum.color_quantization.quantize_colors", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="curriculum.color_quantization.quantize_colors", phase="error", span={"end_byte":1094,"end_column":1,"end_line":42,"start_byte":625,"start_column":1,"start_line":30}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="curriculum.color_quantization.quantize_colors", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            palette = _cott_match_value.value
            return ((len((palette).colors) > 0))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="curriculum.color_quantization.quantize_colors", clause="ensures:1", phase="ensures", span={"end_byte":926,"end_column":57,"end_line":36,"start_byte":874,"start_column":5,"start_line":36}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Palette, ColorQuantizationError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["ColorQuantizationError", "ColorQuantizationError_EmptyPixels", "ColorQuantizationError_ZeroMaxColors", "Palette", "QuantizeRequest", "Rgb", "quantize_colors", "rank_palette_colors"]
