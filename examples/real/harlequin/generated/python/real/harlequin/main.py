from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.harlequin.main_types import LaunchPlan, LaunchPlan_Exit, LaunchPlan_Ide
from real.harlequin.app_types import IdeContext
from real.harlequin.cli_types import HarlequinSettings
from real.harlequin.keymap_types import KeyMap

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def prepare_harlequin(arguments: CottList[str]) -> LaunchPlan:
    """Everything the harlequin command (upstream harlequin.cli.harlequin) does
before the IDE starts, arguments without the program name. Errors are
printed to stderr as "{title}\\n\\n{message}\\n" (a rich.panel.Panel titled
title with a red border when stderr is a terminal) and give Exit(2) unless
stated.
1. real.harlequin.cli.first_pass(arguments).
2. Config: paths = real.harlequin.config.config_search_paths(the typed
config path, else HARLEQUIN_CONFIG_PATH, as Path; Path.cwd(); the
config_dir of real.harlequin.history.harlequin_paths(sys.platform,
Path.home(), os.environ); Path.home()); read each with
real.harlequin.config.read_config_file (Ok(Nothing) skipped) and combine
with real.harlequin.config.merge_config_files.
3. The adapter name is first_pass.adapter, else the adapter entry of the
requested (or default) profile, else "duckdb";
real.harlequin.adapters.find_adapter of it (Nothing: "Harlequin could not
load your adapter." / "No adapter found with name {name}. Installed
adapters: {sorted names joined by ', '}.").
4. real.harlequin.cli.parse_harlequin_arguments(arguments, the names of
real.harlequin.adapters.adapter_descriptors(),
real.harlequin.adapters.adapter_options(kind)); a Usage error prints
"Usage: harlequin [OPTIONS] [CONN_STR]...\\nTry 'harlequin --help' for
help.\\n\\nError: {message}\\n" and gives Exit(2).
5. --version prints real.harlequin.cli.harlequin_version_text(names) to
stdout and gives Exit(0); --help prints
real.harlequin.cli.harlequin_help(descriptors) and gives Exit(0).
6. --config: Exit(real.harlequin.tools.run_config_wizard(typed config path,
the first existing path of step 2 or Path(".harlequin.toml"), the
descriptors, the names of real.harlequin.style.theme_palettes(), the names
of real.harlequin.keymap.builtin_keymaps() and of the merged keymaps)).
7. real.harlequin.config.select_profile(merged, typed profile), then
real.harlequin.config.interpolate_profile(profile, os.environ, its source
file) when Some.
8. --keys: Exit(real.harlequin.tools.run_keys_app(the typed config path,
else the first existing path of step 2, else config_dir/"config.toml"; the
typed keymap names, else the profile's keymap_name, else ["vscode"]; the
builtin keymap names; builtin_keymaps() followed by the merged keymaps)).
9. real.harlequin.cli.resolve_harlequin_settings(profile, parsed,
descriptor, options).
10. real.harlequin.support.apply_locale(settings.locale): Err gives
Exit(2); a warning is printed to stderr and startup continues; the
NumberFormat takes the outcome's separators and grouping.
11. real.harlequin.style.find_theme(settings.theme) (Err: "Harlequin
couldn't load your theme." and its message) and
real.harlequin.keymap.bind_keymaps(builtin_keymaps() followed by the merged
keymaps, settings.keymap_names) (Err: "Harlequin couldn't load your
keymap." and its message) are checked here.
12. With settings.ssh, real.harlequin.support.open_ssh_tunnel (Err:
"Harlequin could not open the SSH tunnel." and its message).
13. Ide(settings, IdeContext(descriptor, paths, palette, number format,
tunnel, os.environ), merged keymaps). In particular, do not name a local
variable `builtins` when binding the builtin keymaps: that identifier is
reserved by the implementation audit for reflection; use base_keymaps."""
    arguments = _cott_normalize_f32_abi(arguments, CottList[str], path="$.arguments")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/main/prepare_harlequin.py", "34135c513cb6e39d8f2ea78f3f5c1802bfbd9a5a09639ec9490b80c7391f8c38", "prepare_harlequin", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.main.prepare_harlequin")
        _result = _implementation(arguments)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.main.prepare_harlequin"
        if _error.span is None:
            _error.span = {"end_byte":4238,"end_column":1,"end_line":75,"start_byte":620,"start_column":1,"start_line":18}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.main.prepare_harlequin", phase="implementation-call", span={"end_byte":4238,"end_column":1,"end_line":75,"start_byte":620,"start_column":1,"start_line":18}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.main.prepare_harlequin", phase="implementation-call", span={"end_byte":4238,"end_column":1,"end_line":75,"start_byte":620,"start_column":1,"start_line":18}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, LaunchPlan, path="$.return")
    _result = _cott_wrap_async_protocol(_result, LaunchPlan, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["LaunchPlan", "LaunchPlan_Exit", "LaunchPlan_Ide", "prepare_harlequin"]
