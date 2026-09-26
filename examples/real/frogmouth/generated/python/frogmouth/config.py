from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_ends_with, _cott_starts_with

from frogmouth.config_types import AppDirectories, Config, Dock, Dock_Left, Dock_Right, Theme, Theme_Dark, Theme_Light

def default_config() -> Config:
    """The configuration used when none is stored: the Dark theme, the Markdown
extensions ".md" then ".markdown", and the sidebar docked Left."""
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/config/default_config.py", "16fde83f0e92f5b47e6283f706fffee86e377c692d80a023347d7155ee9b7802", "default_config", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.config.default_config")
        _result = _implementation()
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.config.default_config"
        if _error.span is None:
            _error.span = {"end_byte":861,"end_column":1,"end_line":40,"start_byte":512,"start_column":1,"start_line":28}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.config.default_config", phase="implementation-call", span={"end_byte":861,"end_column":1,"end_line":40,"start_byte":512,"start_column":1,"start_line":28}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.config.default_config", phase="implementation-call", span={"end_byte":861,"end_column":1,"end_line":40,"start_byte":512,"start_column":1,"start_line":28}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Config, path="$.return")
    if not (_cott_contract_condition((((_result).theme == Theme_Dark())), "frogmouth.config.default_config", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.default_config", clause="ensures:1", phase="ensures", span={"end_byte":747,"end_column":39,"end_line":34,"start_byte":713,"start_column":5,"start_line":34}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).navigation_dock == Dock_Left())), "frogmouth.config.default_config", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.default_config", clause="ensures:2", phase="ensures", span={"end_byte":795,"end_column":48,"end_line":35,"start_byte":752,"start_column":5,"start_line":35}, expected="true", actual="false")
    if not (_cott_contract_condition(((len((_result).markdown_extensions) == 2)), "frogmouth.config.default_config", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.default_config", clause="ensures:3", phase="ensures", span={"end_byte":843,"end_column":48,"end_line":36,"start_byte":800,"start_column":5,"start_line":36}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Config, path="$.return", validator=_cott_validate_abi)
    return _result

def application_directories(home: str, xdg_config_home: Option[str], xdg_data_home: Option[str]) -> AppDirectories:
    """The XDG base directories namespaced as "textualize/frogmouth". The
configuration base is xdg_config_home when it is present and starts with
"/", otherwise home followed by "/.config"; the data base is xdg_data_home
under the same rule, otherwise home followed by "/.local/share". Trailing
"/" characters are removed from a base (keeping a lone "/") before
"/textualize/frogmouth" is appended. No directory is created here."""
    home = _cott_validate_abi(home, str, path="$.home")
    xdg_config_home = _cott_validate_abi(xdg_config_home, Option[str], path="$.xdg_config_home")
    xdg_data_home = _cott_validate_abi(xdg_data_home, Option[str], path="$.xdg_data_home")
    if not (_cott_contract_condition(((len(home) > 0)), "frogmouth.config.application_directories", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.config.application_directories", clause="requires:1", phase="requires", span={"end_byte":1484,"end_column":26,"end_line":54,"start_byte":1463,"start_column":5,"start_line":54}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/config/application_directories.py", "28e06b2d002985c73080a6450c28ab3d380e84207594bc4bf3f2be61bb8a23fa", "application_directories", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.config.application_directories")
        _result = _implementation(home, xdg_config_home, xdg_data_home)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.config.application_directories"
        if _error.span is None:
            _error.span = {"end_byte":2413,"end_column":1,"end_line":67,"start_byte":861,"start_column":1,"start_line":40}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.config.application_directories", phase="implementation-call", span={"end_byte":2413,"end_column":1,"end_line":67,"start_byte":861,"start_column":1,"start_line":40}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.config.application_directories", phase="implementation-call", span={"end_byte":2413,"end_column":1,"end_line":67,"start_byte":861,"start_column":1,"start_line":40}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, AppDirectories, path="$.return")
    if not (_cott_contract_condition((_cott_ends_with((_result).config_directory, "/textualize/frogmouth")), "frogmouth.config.application_directories", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.application_directories", clause="ensures:2", phase="ensures", span={"end_byte":1559,"end_column":74,"end_line":56,"start_byte":1490,"start_column":5,"start_line":56}, expected="true", actual="false")
    if not (_cott_contract_condition((_cott_ends_with((_result).data_directory, "/textualize/frogmouth")), "frogmouth.config.application_directories", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.application_directories", clause="ensures:3", phase="ensures", span={"end_byte":1631,"end_column":72,"end_line":57,"start_byte":1564,"start_column":5,"start_line":57}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = xdg_config_home
        if type(_cott_match_value) is Nothing:
            return (_cott_contract_condition((_cott_starts_with((_result).config_directory, home)), "frogmouth.config.application_directories", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.config.application_directories", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.application_directories", clause="ensures:4", phase="ensures", span={"end_byte":1728,"end_column":97,"end_line":58,"start_byte":1636,"start_column":5,"start_line":58}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = xdg_data_home
        if type(_cott_match_value) is Nothing:
            return (_cott_contract_condition((_cott_starts_with((_result).data_directory, home)), "frogmouth.config.application_directories", "ensures:5"))
        _cott_contract_condition((False), "frogmouth.config.application_directories", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.application_directories", clause="ensures:5", phase="ensures", span={"end_byte":1821,"end_column":93,"end_line":59,"start_byte":1733,"start_column":5,"start_line":59}, expected="true", actual="false")
    def _cott_match_ensures_6() -> bool:
        _cott_match_value = xdg_config_home
        if type(_cott_match_value) is Some and True:
            base = _cott_match_value.value
            return (_cott_contract_condition((((not (_cott_starts_with(base, "/") and (not _cott_ends_with(base, "/")))) or _cott_starts_with((_result).config_directory, base))), "frogmouth.config.application_directories", "ensures:6"))
        _cott_contract_condition((False), "frogmouth.config.application_directories", "ensures:6:applicable")
        return True
    if not (_cott_match_ensures_6()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.application_directories", clause="ensures:6", phase="ensures", span={"end_byte":1980,"end_column":159,"end_line":60,"start_byte":1826,"start_column":5,"start_line":60}, expected="true", actual="false")
    def _cott_match_ensures_7() -> bool:
        _cott_match_value = xdg_data_home
        if type(_cott_match_value) is Some and True:
            base = _cott_match_value.value
            return (_cott_contract_condition((((not (_cott_starts_with(base, "/") and (not _cott_ends_with(base, "/")))) or _cott_starts_with((_result).data_directory, base))), "frogmouth.config.application_directories", "ensures:7"))
        _cott_contract_condition((False), "frogmouth.config.application_directories", "ensures:7:applicable")
        return True
    if not (_cott_match_ensures_7()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.application_directories", clause="ensures:7", phase="ensures", span={"end_byte":2135,"end_column":155,"end_line":61,"start_byte":1985,"start_column":5,"start_line":61}, expected="true", actual="false")
    def _cott_match_ensures_8() -> bool:
        _cott_match_value = xdg_config_home
        if type(_cott_match_value) is Some and True:
            base = _cott_match_value.value
            return (_cott_contract_condition((((not (not _cott_starts_with(base, "/"))) or _cott_starts_with((_result).config_directory, home))), "frogmouth.config.application_directories", "ensures:8"))
        _cott_contract_condition((False), "frogmouth.config.application_directories", "ensures:8:applicable")
        return True
    if not (_cott_match_ensures_8()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.application_directories", clause="ensures:8", phase="ensures", span={"end_byte":2267,"end_column":132,"end_line":62,"start_byte":2140,"start_column":5,"start_line":62}, expected="true", actual="false")
    def _cott_match_ensures_9() -> bool:
        _cott_match_value = xdg_data_home
        if type(_cott_match_value) is Some and True:
            base = _cott_match_value.value
            return (_cott_contract_condition((((not (not _cott_starts_with(base, "/"))) or _cott_starts_with((_result).data_directory, home))), "frogmouth.config.application_directories", "ensures:9"))
        _cott_contract_condition((False), "frogmouth.config.application_directories", "ensures:9:applicable")
        return True
    if not (_cott_match_ensures_9()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.application_directories", clause="ensures:9", phase="ensures", span={"end_byte":2395,"end_column":128,"end_line":63,"start_byte":2272,"start_column":5,"start_line":63}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, AppDirectories, path="$.return", validator=_cott_validate_abi)
    return _result

def toggle_theme(config: Config) -> Config:
    """Switch between the Dark and Light themes (F10)."""
    config = _cott_validate_abi(config, Config, path="$.config")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/config/toggle_theme.py", "1bab463c788ecd7c07891cb6c25c9773c2a098441881d6e51d7ab8a6f0593fef", "toggle_theme", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.config.toggle_theme")
        _result = _implementation(config)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.config.toggle_theme"
        if _error.span is None:
            _error.span = {"end_byte":2641,"end_column":1,"end_line":77,"start_byte":2413,"start_column":1,"start_line":67}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.config.toggle_theme", phase="implementation-call", span={"end_byte":2641,"end_column":1,"end_line":77,"start_byte":2413,"start_column":1,"start_line":67}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.config.toggle_theme", phase="implementation-call", span={"end_byte":2641,"end_column":1,"end_line":77,"start_byte":2413,"start_column":1,"start_line":67}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Config, path="$.return")
    if not (_cott_contract_condition((((_result).markdown_extensions == (config).markdown_extensions)), "frogmouth.config.toggle_theme", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.toggle_theme", clause="ensures:1", phase="ensures", span={"end_byte":2582,"end_column":54,"end_line":72,"start_byte":2533,"start_column":5,"start_line":72}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).navigation_dock == (config).navigation_dock)), "frogmouth.config.toggle_theme", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.toggle_theme", clause="ensures:2", phase="ensures", span={"end_byte":2582,"end_column":54,"end_line":72,"start_byte":2533,"start_column":5,"start_line":72}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).theme != (config).theme)), "frogmouth.config.toggle_theme", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.toggle_theme", clause="ensures:3", phase="ensures", span={"end_byte":2623,"end_column":41,"end_line":73,"start_byte":2587,"start_column":5,"start_line":73}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Config, path="$.return", validator=_cott_validate_abi)
    return _result

def toggle_dock(config: Config) -> Config:
    """Move the navigation sidebar to the other side of the screen."""
    config = _cott_validate_abi(config, Config, path="$.config")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/config/toggle_dock.py", "45518c81caf00cb0ae0ceb2bdabe98f6a2a6e3921043790c3213326896095e7b", "toggle_dock", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.config.toggle_dock")
        _result = _implementation(config)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.config.toggle_dock"
        if _error.span is None:
            _error.span = {"end_byte":2911,"end_column":1,"end_line":87,"start_byte":2641,"start_column":1,"start_line":77}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.config.toggle_dock", phase="implementation-call", span={"end_byte":2911,"end_column":1,"end_line":87,"start_byte":2641,"start_column":1,"start_line":77}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.config.toggle_dock", phase="implementation-call", span={"end_byte":2911,"end_column":1,"end_line":87,"start_byte":2641,"start_column":1,"start_line":77}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Config, path="$.return")
    if not (_cott_contract_condition((((_result).theme == (config).theme)), "frogmouth.config.toggle_dock", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.toggle_dock", clause="ensures:1", phase="ensures", span={"end_byte":2832,"end_column":64,"end_line":82,"start_byte":2773,"start_column":5,"start_line":82}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).markdown_extensions == (config).markdown_extensions)), "frogmouth.config.toggle_dock", "ensures:2")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.toggle_dock", clause="ensures:2", phase="ensures", span={"end_byte":2832,"end_column":64,"end_line":82,"start_byte":2773,"start_column":5,"start_line":82}, expected="true", actual="false")
    if not (_cott_contract_condition((((_result).navigation_dock != (config).navigation_dock)), "frogmouth.config.toggle_dock", "ensures:3")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.config.toggle_dock", clause="ensures:3", phase="ensures", span={"end_byte":2893,"end_column":61,"end_line":83,"start_byte":2837,"start_column":5,"start_line":83}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Config, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["AppDirectories", "Config", "Dock", "Dock_Left", "Dock_Right", "Theme", "Theme_Dark", "Theme_Light", "application_directories", "default_config", "toggle_dock", "toggle_theme"]
