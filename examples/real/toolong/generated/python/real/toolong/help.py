from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.toolong.help_types import HELP_MARKDOWN, HELP_TITLE
from real.toolong.model_types import StyledText

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def help_title(width: U16) -> CottList[StyledText]:
    """The help screen's rainbow title, centered in a content area width cells
wide. The lines are HELP_TITLE.splitlines() (ten lines, the first and last
empty). Line i is colored with the i-th color of
#881177, #aa3355, #cc6666, #ee9944, #eedd00, #99dd55, #44dd88, #22ccbb,
#00bbcc, #0099cc, #3366bb, #663399 (the span's style code is "fg:" + that
color). The title
block is as wide as its widest line (49 cells) and is indented by
max(0, width - 49) // 2 spaces: a non-empty line becomes that many spaces
followed by the line, with one span over the line part; an empty line
stays "" with no spans."""
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/help/help_title.py", "e8b9b7c58c635bbbc5d883324be154f0ce41caa77b6ab11f423fe5f650f2dbe0", "help_title", expected_project_name="toolong", expected_cott_symbol="real.toolong.help.help_title")
        _result = _implementation(width)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.help.help_title"
        if _error.span is None:
            _error.span = {"end_byte":4440,"end_column":1,"end_line":34,"start_byte":3692,"start_column":1,"start_line":16}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.help.help_title", phase="implementation-call", span={"end_byte":4440,"end_column":1,"end_line":34,"start_byte":3692,"start_column":1,"start_line":16}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.help.help_title", phase="implementation-call", span={"end_byte":4440,"end_column":1,"end_line":34,"start_byte":3692,"start_column":1,"start_line":16}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[StyledText], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == 10)), "real.toolong.help.help_title", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.help.help_title", clause="ensures:1", phase="ensures", span={"end_byte":4422,"end_column":29,"end_line":30,"start_byte":4398,"start_column":5,"start_line":30}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[StyledText], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def help_markdown(width: U16) -> Opaque[Literal["toolong.help-markdown"]]:
    """HELP_MARKDOWN rendered for a content area width cells wide, with a
two-cell margin on each side: rich 13.7.0 Markdown(HELP_MARKDOWN) rendered
by a Console(width=max(1, width - 4), color_system="truecolor",
force_terminal=True, file=io.StringIO()) with render_lines(..., pad=False).
Each rendered line becomes a StyledText whose text is two spaces followed
by the line's segment texts with trailing spaces removed, and whose spans
are the non-null segment styles converted like
real.toolong.text.decode_ansi converts rich styles (offsets shifted by the
two-space margin, clipped to the kept text, empty spans dropped). The
result wraps (cott_runtime.Opaque with tag "toolong.help-markdown") a
Python tuple of those real.toolong.model.StyledText values in line order;
it is opaque because the styled document exceeds the facade traversal
bound."""
    width = _cott_normalize_f32_abi(width, U16, path="$.width")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/help/help_markdown.py", "b1ece654f84720daff5e8881020f0212244431bdeb7cab3e2c41b0fc4f231df3", "help_markdown", expected_project_name="toolong", expected_cott_symbol="real.toolong.help.help_markdown")
        _result = _implementation(width)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.help.help_markdown"
        if _error.span is None:
            _error.span = {"end_byte":5437,"end_column":1,"end_line":53,"start_byte":4440,"start_column":1,"start_line":34}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.help.help_markdown", phase="implementation-call", span={"end_byte":5437,"end_column":1,"end_line":53,"start_byte":4440,"start_column":1,"start_line":34}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.help.help_markdown", phase="implementation-call", span={"end_byte":5437,"end_column":1,"end_line":53,"start_byte":4440,"start_column":1,"start_line":34}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Opaque[Literal["toolong.help-markdown"]], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Opaque[Literal["toolong.help-markdown"]], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["HELP_MARKDOWN", "HELP_TITLE", "help_markdown", "help_title"]
