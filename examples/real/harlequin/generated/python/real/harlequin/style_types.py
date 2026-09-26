from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
"""One run of text drawn with one prompt_toolkit style string. style is a space
separated list of "class:<name>" references (for example "class:hq.cell
class:hq.cursor"), or "" for the default style. text never contains LF."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StyledSpan:
    __hash__ = None
    style: str
    text: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "style", _cott_validate_abi(self.style, str, path="$.style"))
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))

"""One screen line. Renderers never emit LF inside a span; the caller joins lines."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StyledLine:
    __hash__ = None
    spans: CottList[StyledSpan]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "spans", _cott_validate_abi(self.spans, CottList[StyledSpan], path="$.spans"))

"""One prompt_toolkit Style rule: selector is a class name such as "hq.cell" or a
built-in prompt_toolkit/pygments class such as "completion-menu" or
"pygments.keyword"; style is a prompt_toolkit style string such as
"fg:#FEFFAC bg:#0C0C0C bold"."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StyleRule:
    __hash__ = None
    selector: str
    style: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "selector", _cott_validate_abi(self.selector, str, path="$.selector"))
        if not _cott_validated_construction():
            object.__setattr__(self, "style", _cott_validate_abi(self.style, str, path="$.style"))

"""The resolved colors of one Harlequin theme, as uppercase "#RRGGBB" strings."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemePalette:
    __hash__ = None
    name: str
    dark: bool
    primary: str
    secondary: str
    accent: str
    foreground: str
    background: str
    surface: str
    panel: str
    warning: str
    error_color: str
    success: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dark", _cott_validate_abi(self.dark, bool, path="$.dark"))
        if not _cott_validated_construction():
            object.__setattr__(self, "primary", _cott_validate_abi(self.primary, str, path="$.primary"))
        if not _cott_validated_construction():
            object.__setattr__(self, "secondary", _cott_validate_abi(self.secondary, str, path="$.secondary"))
        if not _cott_validated_construction():
            object.__setattr__(self, "accent", _cott_validate_abi(self.accent, str, path="$.accent"))
        if not _cott_validated_construction():
            object.__setattr__(self, "foreground", _cott_validate_abi(self.foreground, str, path="$.foreground"))
        if not _cott_validated_construction():
            object.__setattr__(self, "background", _cott_validate_abi(self.background, str, path="$.background"))
        if not _cott_validated_construction():
            object.__setattr__(self, "surface", _cott_validate_abi(self.surface, str, path="$.surface"))
        if not _cott_validated_construction():
            object.__setattr__(self, "panel", _cott_validate_abi(self.panel, str, path="$.panel"))
        if not _cott_validated_construction():
            object.__setattr__(self, "warning", _cott_validate_abi(self.warning, str, path="$.warning"))
        if not _cott_validated_construction():
            object.__setattr__(self, "error_color", _cott_validate_abi(self.error_color, str, path="$.error_color"))
        if not _cott_validated_construction():
            object.__setattr__(self, "success", _cott_validate_abi(self.success, str, path="$.success"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ThemeError_UnknownTheme:
    __hash__ = None
    name: str

ThemeError: TypeAlias = Union[ThemeError_UnknownTheme]

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
"""Return the palette of theme_palettes whose name equals name exactly (theme
names are case sensitive, as in Harlequin). Any other name is
UnknownTheme(name)."""
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
__all__ = ["StyleRule", "StyledLine", "StyledSpan", "ThemeError", "ThemeError_UnknownTheme", "ThemePalette"]
