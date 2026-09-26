from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.config_types import AppDirectories as AppDirectories, Config as Config, Dock as Dock, Dock_Left as Dock_Left, Dock_Right as Dock_Right, Theme as Theme, Theme_Dark as Theme_Dark, Theme_Light as Theme_Light
"""The configuration used when none is stored: the Dark theme, the Markdown
extensions ".md" then ".markdown", and the sidebar docked Left."""
def default_config() -> Config: ...

"""The XDG base directories namespaced as "textualize/frogmouth". The
configuration base is xdg_config_home when it is present and starts with
"/", otherwise home followed by "/.config"; the data base is xdg_data_home
under the same rule, otherwise home followed by "/.local/share". Trailing
"/" characters are removed from a base (keeping a lone "/") before
"/textualize/frogmouth" is appended. No directory is created here."""
def application_directories(home: str, xdg_config_home: Option[str], xdg_data_home: Option[str]) -> AppDirectories: ...

"""Switch between the Dark and Light themes (F10)."""
def toggle_theme(config: Config) -> Config: ...

"""Move the navigation sidebar to the other side of the screen."""
def toggle_dock(config: Config) -> Config: ...

__all__ = ["AppDirectories", "Config", "Dock", "Dock_Left", "Dock_Right", "Theme", "Theme_Dark", "Theme_Light", "application_directories", "default_config", "toggle_dock", "toggle_theme"]
