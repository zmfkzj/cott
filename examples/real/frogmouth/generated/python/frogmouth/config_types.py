from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Theme_Dark:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Theme_Light:
    pass

Theme: TypeAlias = Union[Theme_Dark, Theme_Light]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Dock_Left:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Dock_Right:
    pass

Dock: TypeAlias = Union[Dock_Left, Dock_Right]

"""The viewer configuration: the colour theme, the file suffixes treated as
Markdown, and the screen side the navigation sidebar docks to."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Config:
    __hash__ = None
    theme: Theme
    markdown_extensions: CottList[str]
    navigation_dock: Dock

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "theme", _cott_validate_abi(self.theme, Theme, path="$.theme"))
        if not _cott_validated_construction():
            object.__setattr__(self, "markdown_extensions", _cott_validate_abi(self.markdown_extensions, CottList[str], path="$.markdown_extensions"))
        if not _cott_validated_construction():
            object.__setattr__(self, "navigation_dock", _cott_validate_abi(self.navigation_dock, Dock, path="$.navigation_dock"))

"""Where configuration and application data live. Both are absolute directory
paths in production."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AppDirectories:
    __hash__ = None
    config_directory: str
    data_directory: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "config_directory", _cott_validate_abi(self.config_directory, str, path="$.config_directory"))
        if not _cott_validated_construction():
            object.__setattr__(self, "data_directory", _cott_validate_abi(self.data_directory, str, path="$.data_directory"))

"""The configuration used when none is stored: the Dark theme, the Markdown
extensions ".md" then ".markdown", and the sidebar docked Left."""
"""The XDG base directories namespaced as "textualize/frogmouth". The
configuration base is xdg_config_home when it is present and starts with
"/", otherwise home followed by "/.config"; the data base is xdg_data_home
under the same rule, otherwise home followed by "/.local/share". Trailing
"/" characters are removed from a base (keeping a lone "/") before
"/textualize/frogmouth" is appended. No directory is created here."""
"""Switch between the Dark and Light themes (F10)."""
"""Move the navigation sidebar to the other side of the screen."""
__all__ = ["AppDirectories", "Config", "Dock", "Dock_Left", "Dock_Right", "Theme", "Theme_Dark", "Theme_Light"]
