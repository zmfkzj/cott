from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_unique_by

from real.harlequin.style_types import StyleRule, StyledLine, StyledSpan, ThemeError, ThemeError_UnknownTheme, ThemePalette

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def theme_palettes() -> CottList[ThemePalette]:
    """The themes the --theme option accepts, in this exact order, with these exact
resolved colors (columns: name | dark/light | primary | secondary | accent |
foreground | background | surface | panel | warning | error_color | success). The
first is Harlequin's own theme; the rest are the resolved palettes of the
Textual 8.2.8 built-in themes Harlequin 2.15.0 accepts (its ansi-dark and
ansi-light passthrough themes are not accepted).
harlequin | dark | #FEFFAC | #45FFCA | #FFB6D9 | #DDDDDD | #0C0C0C | #0C0C0C | #555555 | #FEFFAC | #FFB6D9 | #45FFCA
textual-dark | dark | #0178D4 | #004578 | #FEA62B | #E0E0E0 | #121212 | #1E1E1E | #242F38 | #FEA62B | #B93C5B | #4EBF71
textual-light | light | #004578 | #0178D4 | #FEA62B | #1F1F1F | #E0E0E0 | #D8D8D8 | #D0D0D0 | #FEA62B | #B93C5B | #4EBF71
nord | dark | #88C0D0 | #81A1C1 | #B48EAD | #D8DEE9 | #2E3440 | #3B4252 | #434C5E | #EACB8B | #BE616A | #A3BE8C
gruvbox | dark | #85A598 | #A89A85 | #F9BD2F | #FBF1C7 | #282828 | #3C3836 | #504945 | #FD8019 | #FA4934 | #B7BB26
catppuccin-mocha | dark | #F5C2E7 | #CBA6F7 | #F9B387 | #CDD6F4 | #181825 | #313244 | #45475A | #FAE3B0 | #F28FAD | #ABE9B3
dracula | dark | #BD93F9 | #6272A4 | #FF79C6 | #F8F8F2 | #282A36 | #2B2E3B | #313442 | #FEB86C | #FE5555 | #50FA7B
tokyo-night | dark | #BB9AF7 | #7AA2F7 | #FE9E64 | #A9B1D6 | #1A1B26 | #24283B | #414868 | #DFAF68 | #F6768E | #9ECE6A
monokai | dark | #AE81FF | #F82672 | #66D9EF | #D6D6D6 | #272822 | #2E2E2E | #3E3D32 | #FC971F | #F82672 | #A5E22E
flexoki | dark | #205EA6 | #24837B | #9B76C8 | #FFFCF0 | #100F0F | #1C1B1A | #282726 | #AC8301 | #AE3029 | #65800B
catppuccin-latte | light | #8839EF | #DB8A78 | #FD640B | #4C4F69 | #EFF1F5 | #E6E9EF | #CCD0DA | #DE8E1D | #D10F39 | #40A02B
catppuccin-frappe | dark | #CA9EE6 | #EE9F76 | #F4B8E4 | #C6D0F5 | #303446 | #414559 | #51576D | #E4C890 | #E68284 | #A6D189
catppuccin-macchiato | dark | #C6A0F6 | #F4A97F | #F5BDE6 | #CAD3F5 | #24273A | #363A4F | #494D64 | #EED49F | #ED8796 | #A6DA95
solarized-light | light | #268BD2 | #2AA198 | #6C71C4 | #586E75 | #FDF6E3 | #EEE8D5 | #EEE8D5 | #CA4B16 | #DB322F | #849900
solarized-dark | dark | #268BD2 | #2AA198 | #6C71C4 | #839496 | #002B36 | #073642 | #073642 | #CA4B16 | #DB322F | #849900
rose-pine | dark | #C4A7E7 | #31748F | #EBBCBA | #E0DEF4 | #191724 | #1F1D2E | #26233A | #F5C177 | #EA6F92 | #9CCFD8
rose-pine-moon | dark | #C4A7E7 | #3E8FB0 | #EA9A97 | #E0DEF4 | #232136 | #2A273F | #393552 | #F5C177 | #EA6F92 | #9CCFD8
rose-pine-dawn | light | #907AA9 | #286983 | #D6827E | #575279 | #FAF4ED | #FFFAF3 | #F2E9E1 | #E99D34 | #B4637A | #56949F
atom-one-dark | dark | #61AFEF | #C678DD | #A378C2 | #ABB2BF | #282C34 | #3B414D | #4F5666 | #DDB25B | #EF6262 | #62F062
atom-one-light | light | #4078F2 | #A626A4 | #BE9232 | #383A42 | #FAFAFA | #E0E0E0 | #CCCCCC | #D7D938 | #F13F3F | #6BF23F"""
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/style/theme_palettes.py", "3d7b23f3d795c448135e29f5f9a183285dc0adf6342de8463399f095cf73cda9", "theme_palettes", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.style.theme_palettes")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.style.theme_palettes"
        if _error.span is None:
            _error.span = {"end_byte":4223,"end_column":1,"end_line":83,"start_byte":1123,"start_column":1,"start_line":48}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.style.theme_palettes", phase="implementation-call", span={"end_byte":4223,"end_column":1,"end_line":83,"start_byte":1123,"start_column":1,"start_line":48}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.style.theme_palettes", phase="implementation-call", span={"end_byte":4223,"end_column":1,"end_line":83,"start_byte":1123,"start_column":1,"start_line":48}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[ThemePalette], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == 20)), "real.harlequin.style.theme_palettes", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.style.theme_palettes", clause="ensures:1", phase="ensures", span={"end_byte":4156,"end_column":29,"end_line":78,"start_byte":4132,"start_column":5,"start_line":78}, expected="true", actual="false")
        if not (_cott_contract_condition((_cott_unique_by(_result, "name")), "real.harlequin.style.theme_palettes", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.style.theme_palettes", clause="ensures:2", phase="ensures", span={"end_byte":4205,"end_column":49,"end_line":79,"start_byte":4161,"start_column":5,"start_line":79}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[ThemePalette], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def find_theme(name: str) -> Result[ThemePalette, ThemeError]:
    """Return the palette of theme_palettes whose name equals name exactly (theme
names are case sensitive, as in Harlequin). Any other name is
UnknownTheme(name)."""
    name = _cott_normalize_f32_abi(name, str, path="$.name")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/style/find_theme.py", "6fd6b900ad15f60e8d9f6c015b2a161898ca0e73c31525cd91e1940d343968a8", "find_theme", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.style.find_theme")
        _result = _implementation(name)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.style.find_theme"
        if _error.span is None:
            _error.span = {"end_byte":4658,"end_column":1,"end_line":97,"start_byte":4223,"start_column":1,"start_line":83}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.style.find_theme", phase="implementation-call", span={"end_byte":4658,"end_column":1,"end_line":97,"start_byte":4223,"start_column":1,"start_line":83}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.style.find_theme", phase="implementation-call", span={"end_byte":4658,"end_column":1,"end_line":97,"start_byte":4223,"start_column":1,"start_line":83}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[ThemePalette, ThemeError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.style.find_theme", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (ThemeError_UnknownTheme,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.style.find_theme", phase="error", span={"end_byte":4658,"end_column":1,"end_line":97,"start_byte":4223,"start_column":1,"start_line":83}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.style.find_theme", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.style.find_theme", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is ThemeError_UnknownTheme:
            _cott_contract_condition(True, "real.harlequin.style.find_theme", "error:3")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                palette = _cott_match_value.value
                return (_cott_contract_condition((((palette).name == name)), "real.harlequin.style.find_theme", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.style.find_theme", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.style.find_theme", clause="ensures:1", phase="ensures", span={"end_byte":4529,"end_column":55,"end_line":90,"start_byte":4479,"start_column":5,"start_line":90}, expected="true", actual="false")
        def _cott_match_ensures_2() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Err and type(_cott_match_value.error) is ThemeError_UnknownTheme and True:
                unknown = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
                return (_cott_contract_condition(((unknown == name)), "real.harlequin.style.find_theme", "ensures:2"))
            _cott_contract_condition((False), "real.harlequin.style.find_theme", "ensures:2:applicable")
            return True
        if not (_cott_match_ensures_2()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.style.find_theme", clause="ensures:2", phase="ensures", span={"end_byte":4605,"end_column":76,"end_line":91,"start_byte":4534,"start_column":5,"start_line":91}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[ThemePalette, ThemeError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def theme_style_rules(palette: ThemePalette) -> CottList[StyleRule]:
    """Derive the complete prompt_toolkit style for the IDE from palette. Return one
rule per selector below, in this order, with exactly these style strings, where
P, S, A, F, B, U, N, W, E and G stand for primary, secondary, accent,
foreground, background, surface, panel, warning, error_color and success.
"" -> "fg:F bg:B"
hq.text -> "fg:F bg:B"
hq.muted -> "fg:N bg:B" when N differs from B, else "fg:F bg:B italic"
hq.border -> "fg:N bg:B"
hq.border.focused -> "fg:P bg:B"
hq.title -> "fg:N bg:B bold"
hq.title.focused -> "fg:P bg:B bold"
hq.tab -> "fg:F bg:U"
hq.tab.active -> "fg:B bg:P bold"
hq.header -> "fg:P bg:U bold"
hq.cell -> "fg:F bg:B"
hq.cell.null -> "fg:N bg:B italic"
hq.cell.number -> "fg:S bg:B"
hq.cursor -> "fg:B bg:A bold"
hq.selection -> "fg:B bg:S"
hq.rownumber -> "fg:N bg:B"
hq.tree.label -> "fg:F bg:B"
hq.tree.type -> "fg:N bg:B italic"
hq.tree.guide -> "fg:N bg:B"
hq.footer -> "fg:F bg:U"
hq.footer.key -> "fg:P bg:U bold"
hq.footer.description -> "fg:F bg:U"
hq.status -> "fg:F bg:U"
hq.error -> "fg:E bg:B bold"
hq.warning -> "fg:W bg:B bold"
hq.success -> "fg:G bg:B bold"
hq.notification -> "fg:F bg:N"
hq.notification.error -> "fg:B bg:E bold"
hq.dialog -> "fg:F bg:U"
hq.dialog.title -> "fg:P bg:U bold"
hq.input -> "fg:F bg:B"
hq.button -> "fg:F bg:N"
hq.button.focused -> "fg:B bg:P bold"
hq.match -> "fg:A bg:B bold underline"
hq.loading -> "fg:A bg:B bold"
line-number -> "fg:N bg:B"
line-number.current -> "fg:P bg:B bold"
selected -> "fg:B bg:S"
search -> "fg:B bg:W"
search.current -> "fg:B bg:A"
completion-menu -> "fg:F bg:N"
completion-menu.completion.current -> "fg:B bg:P bold"
completion-menu.meta.completion -> "fg:F bg:U"
completion-menu.meta.completion.current -> "fg:B bg:P"
scrollbar.background -> "bg:U"
scrollbar.button -> "bg:N"
frame.border -> "fg:N"
frame.label -> "fg:P bold"
dialog -> "fg:F bg:B"
dialog.body -> "fg:F bg:U"
dialog frame.label -> "fg:P bold"
button -> "fg:F bg:N"
button.focused -> "fg:B bg:P bold"
text-area -> "fg:F bg:B"
pygments.keyword -> "fg:P bold"
pygments.name.builtin -> "fg:S"
pygments.name.function -> "fg:S"
pygments.literal.string -> "fg:G"
pygments.literal.number -> "fg:A"
pygments.comment -> "fg:N italic"
pygments.operator -> "fg:A"
pygments.punctuation -> "fg:F"
pygments.name -> "fg:F"."""
    palette = _cott_normalize_f32_abi(palette, ThemePalette, path="$.palette")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/style/theme_style_rules.py", "484ffab2fb7b9d142afdc0e6e71a5158eb9110386dde63f533007281af6c7411", "theme_style_rules", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.style.theme_style_rules")
        _result = _implementation(palette)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.style.theme_style_rules"
        if _error.span is None:
            _error.span = {"end_byte":7388,"end_column":1,"end_line":173,"start_byte":4658,"start_column":1,"start_line":97}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.style.theme_style_rules", phase="implementation-call", span={"end_byte":7388,"end_column":1,"end_line":173,"start_byte":4658,"start_column":1,"start_line":97}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.style.theme_style_rules", phase="implementation-call", span={"end_byte":7388,"end_column":1,"end_line":173,"start_byte":4658,"start_column":1,"start_line":97}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[StyleRule], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == 63)), "real.harlequin.style.theme_style_rules", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.style.theme_style_rules", clause="ensures:1", phase="ensures", span={"end_byte":7320,"end_column":29,"end_line":168,"start_byte":7296,"start_column":5,"start_line":168}, expected="true", actual="false")
        if not (_cott_contract_condition((_cott_unique_by(_result, "selector")), "real.harlequin.style.theme_style_rules", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.style.theme_style_rules", clause="ensures:2", phase="ensures", span={"end_byte":7370,"end_column":50,"end_line":169,"start_byte":7325,"start_column":5,"start_line":169}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[StyleRule], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["StyleRule", "StyledLine", "StyledSpan", "ThemeError", "ThemeError_UnknownTheme", "ThemePalette", "find_theme", "theme_palettes", "theme_style_rules"]
