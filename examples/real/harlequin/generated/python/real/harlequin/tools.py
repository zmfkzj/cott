from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.harlequin.tools_types import KeyRow, WizardAnswers
from real.harlequin.adapters_types import AdapterDescriptor, AdapterOption, AdapterSetting
from real.harlequin.config_types import ConfigEntry, Profile
from real.harlequin.keymap_types import KeyMap

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def keymap_rows(available: CottList[KeyMap], active: CottList[str]) -> CottList[KeyRow]:
    """The keymap editor's table (upstream HarlequinKeys): one row per action of
real.harlequin.keymap.harlequin_actions(scope) over every ActionScope,
ordered by ActionSpec.position (the upstream table order). For each active
keymap name in order that names a keymap in available (missing names are
skipped), every binding adds the comma-separated keys of binding.keys
(stripped, empty pieces dropped) to its action's row, and a binding with a
nonempty key_display replaces the row's key_display (the last one wins).
Each row's keys are unique and sorted. The title joins the scope title
("App", "Code Editor", "Data Catalog", "Results Viewer", "History Screen",
...) and the action description with ": ". Unbound actions have no keys."""
    available = _cott_normalize_f32_abi(available, CottList[KeyMap], path="$.available")
    active = _cott_normalize_f32_abi(active, CottList[str], path="$.active")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/tools/keymap_rows.py", "cf602fc0e10233f11fb623a00c00407139ae938b2454f3f13de11a06d56fa1f5", "keymap_rows", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.tools.keymap_rows")
        _result = _implementation(available, active)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.tools.keymap_rows"
        if _error.span is None:
            _error.span = {"end_byte":2325,"end_column":1,"end_line":60,"start_byte":1442,"start_column":1,"start_line":44}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.tools.keymap_rows", phase="implementation-call", span={"end_byte":2325,"end_column":1,"end_line":60,"start_byte":1442,"start_column":1,"start_line":44}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.tools.keymap_rows", phase="implementation-call", span={"end_byte":2325,"end_column":1,"end_line":60,"start_byte":1442,"start_column":1,"start_line":44}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[KeyRow], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[KeyRow], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def edit_row_keys(row: KeyRow, keys: CottList[str], key_display: str) -> KeyRow:
    """The row after the binding editor's Submit: keys made unique and sorted
(empty strings dropped), key_display Nothing when blank, else the text."""
    row = _cott_normalize_f32_abi(row, KeyRow, path="$.row")
    keys = _cott_normalize_f32_abi(keys, CottList[str], path="$.keys")
    key_display = _cott_normalize_f32_abi(key_display, str, path="$.key_display")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/tools/edit_row_keys.py", "2042c0bee4aca9dfb0568614e6ef0f6fa0e37bf1025faaa056f05d6c887ef46a", "edit_row_keys", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.tools.edit_row_keys")
        _result = _implementation(row, keys, key_display)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.tools.edit_row_keys"
        if _error.span is None:
            _error.span = {"end_byte":2660,"end_column":1,"end_line":70,"start_byte":2325,"start_column":1,"start_line":60}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.tools.edit_row_keys", phase="implementation-call", span={"end_byte":2660,"end_column":1,"end_line":70,"start_byte":2325,"start_column":1,"start_line":60}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.tools.edit_row_keys", phase="implementation-call", span={"end_byte":2660,"end_column":1,"end_line":70,"start_byte":2325,"start_column":1,"start_line":60}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, KeyRow, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((((_result).action == (row).action) and ((_result).title == (row).title))), "real.harlequin.tools.edit_row_keys", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.tools.edit_row_keys", clause="ensures:1", phase="ensures", span={"end_byte":2642,"end_column":70,"end_line":66,"start_byte":2577,"start_column":5,"start_line":66}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, KeyRow, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def rows_to_keymap(name: str, rows: CottList[KeyRow]) -> KeyMap:
    """The keymap the editor saves: named name, with one KeyBinding per row whose
keys are nonempty or whose key_display is set, in row order; keys joined
with "," and key_display copied."""
    name = _cott_normalize_f32_abi(name, str, path="$.name")
    rows = _cott_normalize_f32_abi(rows, CottList[KeyRow], path="$.rows")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/tools/rows_to_keymap.py", "b4b128088ab887b255dc9ab3f84c3d45b8d4ad043025e90c279e99422ed92abc", "rows_to_keymap", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.tools.rows_to_keymap")
        _result = _implementation(name, rows)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.tools.rows_to_keymap"
        if _error.span is None:
            _error.span = {"end_byte":2983,"end_column":1,"end_line":81,"start_byte":2660,"start_column":1,"start_line":70}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.tools.rows_to_keymap", phase="implementation-call", span={"end_byte":2983,"end_column":1,"end_line":81,"start_byte":2660,"start_column":1,"start_line":70}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.tools.rows_to_keymap", phase="implementation-call", span={"end_byte":2983,"end_column":1,"end_line":81,"start_byte":2660,"start_column":1,"start_line":70}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, KeyMap, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).name == name)), "real.harlequin.tools.rows_to_keymap", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.tools.rows_to_keymap", clause="ensures:1", phase="ensures", span={"end_byte":2965,"end_column":32,"end_line":77,"start_byte":2938,"start_column":5,"start_line":77}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, KeyMap, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def keymap_name_problem(name: str, builtin_names: CottList[str]) -> Option[str]:
    """The keymap-name validator of the save dialog: Some("Cannot use the name of
an existing keymap plug-in") when name equals a builtin keymap name, Some(
"Cannot be empty") when name is blank, else Nothing."""
    name = _cott_normalize_f32_abi(name, str, path="$.name")
    builtin_names = _cott_normalize_f32_abi(builtin_names, CottList[str], path="$.builtin_names")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/tools/keymap_name_problem.py", "77c569bd02b8c897af47a3f6792f8a0e8a094dafb51166a675ba7ac0c7ab51e3", "keymap_name_problem", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.tools.keymap_name_problem")
        _result = _implementation(name, builtin_names)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.tools.keymap_name_problem"
        if _error.span is None:
            _error.span = {"end_byte":3311,"end_column":1,"end_line":90,"start_byte":2983,"start_column":1,"start_line":81}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.tools.keymap_name_problem", phase="implementation-call", span={"end_byte":3311,"end_column":1,"end_line":90,"start_byte":2983,"start_column":1,"start_line":81}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.tools.keymap_name_problem", phase="implementation-call", span={"end_byte":3311,"end_column":1,"end_line":90,"start_byte":2983,"start_column":1,"start_line":81}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Option[str], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Option[str], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def run_keys_app(save_path: Path, active: CottList[str], builtin_names: CottList[str], available: CottList[KeyMap]) -> I64:
    """The `harlequin --keys` editor as one full-screen lock-selected
prompt_toolkit Application built without classes. The screen shows the
instruction "The table below shows the active key bindings loaded from your
config. Edit the key bindings, then quit to save them to a keymap." and
"Loaded Keymaps: {', '.join(active)}", then the table of
keymap_rows(available, active) with columns "Action", "Keys" (keys joined
with ", ", each shown through real.harlequin.keymap.key_label) and "Key
Display", one row highlighted (up/down/pageup/pagedown/home/end move).
enter opens the binding editor for the row: "Use the buttons below to
replace, remove, or add bindings for this action." and "Enter: Select
Button; Tab: Next Button", one "Edit" and "Remove" button per key, an "Add
Key" button, a "Key Display" input, and "Submit"/"Cancel". Edit and Add Key
show "Press a key combination" and capture the next key press as its
Textual key name (ctrl+x, shift+tab, f5, a, ...). Submit applies
edit_row_keys; Cancel keeps the row.
ctrl+q quits: without changes the app returns 0 at once; with changes a
quit dialog offers "Keep Editing", "Discard + Quit" and "Save + Quit" with
inputs for the keymap name (initially the last active name) and the file
path (initially save_path; must not be a directory). Save validates the
name with keymap_name_problem, writes rows_to_keymap(name, rows) with
real.harlequin.config.write_keymap(path, keymap), and after the screen is
restored prints "Keymap {name} written to file at {path}" then "Use it
with: harlequin --keymap-name {name}" or in a profile
"keymap_name=['{name}']" under the title "Keymap successfully created";
a ConfigError prints its title and message to stderr and returns 2.
Returns 0 otherwise."""
    save_path = _cott_normalize_f32_abi(save_path, Path, path="$.save_path")
    active = _cott_normalize_f32_abi(active, CottList[str], path="$.active")
    builtin_names = _cott_normalize_f32_abi(builtin_names, CottList[str], path="$.builtin_names")
    available = _cott_normalize_f32_abi(available, CottList[KeyMap], path="$.available")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/tools/run_keys_app.py", "fa9701ac074c42a3c0082c4f52cc1e2a337930241525660dae0ec55149ec99a5", "run_keys_app", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.tools.run_keys_app")
        _result = _implementation(save_path, active, builtin_names, available)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.tools.run_keys_app"
        if _error.span is None:
            _error.span = {"end_byte":5329,"end_column":1,"end_line":122,"start_byte":3311,"start_column":1,"start_line":90}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.tools.run_keys_app", phase="implementation-call", span={"end_byte":5329,"end_column":1,"end_line":122,"start_byte":3311,"start_column":1,"start_line":90}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.tools.run_keys_app", phase="implementation-call", span={"end_byte":5329,"end_column":1,"end_line":122,"start_byte":3311,"start_column":1,"start_line":90}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, I64, path="$.return")
    _result = _cott_wrap_async_protocol(_result, I64, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def wizard_profile(answers: WizardAnswers, adapter_option_list: CottList[AdapterOption]) -> Profile:
    """The profile the config wizard writes (upstream _prompt_to_create_profile):
named answers.profile_name, entries in this order: adapter (Text),
conn_str (Array of Text from shlex.split, only when nonblank), read_only
(Boolean true, only when true), theme (Text), viewer_max_rows (Integer,
only when blank-stripped text is a whole number >= 0; blank or invalid
answers omit it so profile resolution retains its 100000-row default),
keymap_name (Array of Text), limit (Integer, only when blank-stripped text
is an integer >= 0), show_files, show_s3,
locale (Text, only when nonblank), then when use_ssh: ssh_host (stripped
Text), ssh_forward (Array of Text from shlex.split, only when nonblank),
ssh_batch_mode (Boolean true, only when true), ssh_timeout (Real, only when
nonblank), then each adapter option answer in adapter_option_list order
under its profile key (name with "-" replaced by "_"): Text answers only
when nonblank, Flag answers always (false included) as Boolean, Values
answers as Array of Text only when nonempty."""
    answers = _cott_normalize_f32_abi(answers, WizardAnswers, path="$.answers")
    adapter_option_list = _cott_normalize_f32_abi(adapter_option_list, CottList[AdapterOption], path="$.adapter_option_list")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/tools/wizard_profile.py", "42df81dff04b8fec85fe2090f037df4c4019fdc69dcfda14feb02de798b3c433", "wizard_profile", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.tools.wizard_profile")
        _result = _implementation(answers, adapter_option_list)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.tools.wizard_profile"
        if _error.span is None:
            _error.span = {"end_byte":6636,"end_column":1,"end_line":146,"start_byte":5329,"start_column":1,"start_line":122}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.tools.wizard_profile", phase="implementation-call", span={"end_byte":6636,"end_column":1,"end_line":146,"start_byte":5329,"start_column":1,"start_line":122}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.tools.wizard_profile", phase="implementation-call", span={"end_byte":6636,"end_column":1,"end_line":146,"start_byte":5329,"start_column":1,"start_line":122}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Profile, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).name == (answers).profile_name)), "real.harlequin.tools.wizard_profile", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.tools.wizard_profile", clause="ensures:1", phase="ensures", span={"end_byte":6582,"end_column":48,"end_line":141,"start_byte":6539,"start_column":5,"start_line":141}, expected="true", actual="false")
        if not (_cott_contract_condition(((len((_result).entries) >= 4)), "real.harlequin.tools.wizard_profile", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.tools.wizard_profile", clause="ensures:2", phase="ensures", span={"end_byte":6618,"end_column":36,"end_line":142,"start_byte":6587,"start_column":5,"start_line":142}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Profile, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def run_config_wizard(explicit_path: Option[Path], default_path: Path, descriptors: CottList[AdapterDescriptor], theme_names: CottList[str], keymap_names: CottList[str]) -> I64:
    """The `harlequin --config` wizard, with the lock-selected questionary.
With explicit_path print "Updating the file at {path}:" and use it;
otherwise ask "What config file do you want to create or update?" (path
question, default default_path, must end in ".toml", "~" expanded, made
absolute); a non-.toml explicit path prints "Harlequin could not create
your configuration." and "Must create a file with a .toml extension." to
stderr and returns 0. Read the file with
real.harlequin.config.read_config_file (a ConfigError prints and returns 0). Questions in order,
each defaulting to the chosen profile's existing value: "Which profile
would you like to update?" (select: "[Create a New Profile]" then the
existing names; only when profiles exist) and, for a new profile, "What
would you like to name your profile?" (validator "Cannot be empty or
None"); "Which adapter should this profile use?" (select of the sorted
descriptor names, default the profile's or "duckdb"); "What connection
string(s) should this profile use?" (instruction "Separate items by a
space. Quote a single item containing spaces."); "Should this profile
connect read-only?" (confirm, only when implements_read_only); "What theme
should this profile use?" (select of theme_names, default "harlequin");
"Which keymaps would you like to use?" (checkbox of keymap_names, default
["vscode"]); "How many rows should each query fetch from the database?"
("Leave blank for app defaults; enter -1 for no limit."); "How many rows
should the Results Viewer hold?" ("Enter -1 for no limit.", default
"100000", integer validator); "Show local files from a directory? (Leave
blank to hide)"; "Show cloud storage files?"; "What locale should
Harlequin use for formatting numbers?" ("Leave blank to use the system
locale."); "Do you connect via SSH?" and when yes the destination (nonblank,
"Cannot be empty"), forwards, "Use SSH BatchMode?" and "How many seconds
should Harlequin wait for the forwards?"; "Which of the following adapter
options would you like to set?" (checkbox of real.harlequin.adapters.adapter_options((kind) labels,
checked when the profile has the key) then one question per selected option
(password question for secret options, confirm for flags, select for
choices, text otherwise); "Would you like to set a default profile?"
(select "[No default]" then the profile names). Then print the preview
real.harlequin.config.profile_toml(profile, secret option names) of
wizard_profile(answers, options) and ask "Save this profile?"; yes writes
real.harlequin.config.write_profile(path, profile, default profile) and
prints "Profile {name} written to {path}". A KeyboardInterrupt or a None
answer anywhere prints "Cancelled config updates. No changes were made to
any files." and returns 0. Always returns 0."""
    explicit_path = _cott_normalize_f32_abi(explicit_path, Option[Path], path="$.explicit_path")
    default_path = _cott_normalize_f32_abi(default_path, Path, path="$.default_path")
    descriptors = _cott_normalize_f32_abi(descriptors, CottList[AdapterDescriptor], path="$.descriptors")
    theme_names = _cott_normalize_f32_abi(theme_names, CottList[str], path="$.theme_names")
    keymap_names = _cott_normalize_f32_abi(keymap_names, CottList[str], path="$.keymap_names")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/tools/run_config_wizard.py", "b7bca069c53f0a4d537620f7b5d2d478cb7fd20c6a698d947a89661748d10ff4", "run_config_wizard", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.tools.run_config_wizard")
        _result = _implementation(explicit_path, default_path, descriptors, theme_names, keymap_names)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.tools.run_config_wizard"
        if _error.span is None:
            _error.span = {"end_byte":9806,"end_column":1,"end_line":190,"start_byte":6636,"start_column":1,"start_line":146}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.tools.run_config_wizard", phase="implementation-call", span={"end_byte":9806,"end_column":1,"end_line":190,"start_byte":6636,"start_column":1,"start_line":146}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.tools.run_config_wizard", phase="implementation-call", span={"end_byte":9806,"end_column":1,"end_line":190,"start_byte":6636,"start_column":1,"start_line":146}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, I64, path="$.return")
    _result = _cott_wrap_async_protocol(_result, I64, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["KeyRow", "WizardAnswers", "edit_row_keys", "keymap_name_problem", "keymap_rows", "rows_to_keymap", "run_config_wizard", "run_keys_app", "wizard_profile"]
