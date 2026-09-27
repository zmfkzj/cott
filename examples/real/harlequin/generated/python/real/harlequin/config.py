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

from real.harlequin.config_types import AdapterOptionSet, ConfigEntry, ConfigError, ConfigError_Invalid, ConfigFile, ConfigProblem, ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Integer, ConfigValue_Real, ConfigValue_Table, ConfigValue_Text, MergedConfig, Profile, ProfileSource
from real.harlequin.adapters_types import AdapterOption
from real.harlequin.keymap_types import KeyMap

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def config_search_paths(explicit: Option[Path], cwd: Path, user_config_dir: Path, home: Path) -> CottList[Path]:
    """The config files Harlequin looks for, nearest (highest priority) first:
explicit when given; then cwd/harlequin.toml, cwd/.harlequin.toml,
cwd/pyproject.toml; then user_config_dir/harlequin.toml,
user_config_dir/.harlequin.toml, user_config_dir/config.toml; then
home/harlequin.toml, home/.harlequin.toml, home/pyproject.toml. No
deduplication is performed."""
    explicit = _cott_normalize_f32_abi(explicit, Option[Path], path="$.explicit")
    cwd = _cott_normalize_f32_abi(cwd, Path, path="$.cwd")
    user_config_dir = _cott_normalize_f32_abi(user_config_dir, Path, path="$.user_config_dir")
    home = _cott_normalize_f32_abi(home, Path, path="$.home")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/config/config_search_paths.py", "4d284eb8c4856c07944435a4cb12e1ca22f2e31839186677d627d73182b5a2b5", "config_search_paths", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.config.config_search_paths")
        _result = _implementation(explicit, cwd, user_config_dir, home)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.config.config_search_paths"
        if _error.span is None:
            _error.span = {"end_byte":2657,"end_column":1,"end_line":97,"start_byte":2082,"start_column":1,"start_line":78}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.config.config_search_paths", phase="implementation-call", span={"end_byte":2657,"end_column":1,"end_line":97,"start_byte":2082,"start_column":1,"start_line":78}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.config.config_search_paths", phase="implementation-call", span={"end_byte":2657,"end_column":1,"end_line":97,"start_byte":2082,"start_column":1,"start_line":78}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[Path], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) >= 9)), "real.harlequin.config.config_search_paths", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.config.config_search_paths", clause="ensures:1", phase="ensures", span={"end_byte":2639,"end_column":28,"end_line":93,"start_byte":2616,"start_column":5,"start_line":93}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[Path], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def read_config_file(path: Path) -> Result[Option[ConfigFile], ConfigError]:
    """Read one config file with tomllib. A path that does not exist is Ok(Nothing);
so is a file that cannot be read (OSError is treated as empty content, as in
Harlequin). A file named pyproject.toml contributes only its [tool.harlequin]
table (absent means a file that defines nothing); any other file is read as a
whole.
Allowed top-level keys are exactly default_profile (string), profiles (table
of tables) and keymaps (table of arrays of binding tables with keys "keys"
and "action" strings and optional "key_display" string). Profile tables keep
their keys and values in file order, converting TOML values to ConfigValue
(dates and times become Text of their ISO form). Keymaps become KeyMap values
with KeyBinding(keys, action, key_display).
Errors are Invalid(title, message):
- TOML syntax: title "Harlequin could not load the config file.", message
  "Attempted to load the config file at {path}, but encountered an
  error:\\n\\n{error}".
- an unknown top-level key: title "Harlequin couldn't load your config file.",
  message "Found unexpected key in config: {key}\\nFound in the config file at
  {path}.".
- default_profile not a string, profiles not a table of tables, keymaps not a
  table of arrays: title "Harlequin couldn't load your config file.", message
  "Expected `{table|string|array}`, got `{toml type}` at {dotted key}.\\nFound
  in the config file at {path}." (TOML type names: table, string, integer,
  number, boolean, array).
- a profile named exactly "None": same title, message "Config file defines a
  profile named 'None', which is not allowed\\nFound in the config file at
  {path}.".
- a binding with another property: title "Harlequin could not load your
  keymap.", message "Key bindings must be defined in config files with only
  three properties: `keys`, `action`, and `key_profile`. Got a binding in the
  map named {name} that tried to define a property: '{property}'"."""
    path = _cott_normalize_f32_abi(path, Path, path="$.path")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/config/read_config_file.py", "ffb4b887e3269ed907cdc5b68990ae33c7bb085b7e5c974ac00e5ed9c0d2fa6b", "read_config_file", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.config.read_config_file")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.config.read_config_file"
        if _error.span is None:
            _error.span = {"end_byte":4872,"end_column":1,"end_line":137,"start_byte":2657,"start_column":1,"start_line":97}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.config.read_config_file", phase="implementation-call", span={"end_byte":4872,"end_column":1,"end_line":137,"start_byte":2657,"start_column":1,"start_line":97}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.config.read_config_file", phase="implementation-call", span={"end_byte":4872,"end_column":1,"end_line":137,"start_byte":2657,"start_column":1,"start_line":97}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Option[ConfigFile], ConfigError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.config.read_config_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (ConfigError_Invalid,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.config.read_config_file", phase="error", span={"end_byte":4872,"end_column":1,"end_line":137,"start_byte":2657,"start_column":1,"start_line":97}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.config.read_config_file", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.config.read_config_file", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is ConfigError_Invalid:
            _cott_contract_condition(True, "real.harlequin.config.read_config_file", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                found = _cott_match_value.value
                return (_cott_contract_condition((True), "real.harlequin.config.read_config_file", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.config.read_config_file", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.config.read_config_file", clause="ensures:1", phase="ensures", span={"end_byte":4814,"end_column":37,"end_line":131,"start_byte":4782,"start_column":5,"start_line":131}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Option[ConfigFile], ConfigError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def merge_config_files(files: CottList[ConfigFile]) -> MergedConfig:
    """Merge files given nearest first, as MergedConfig documents: the first
non-Nothing default_profile wins (with its file as default_source); for every
profile name and keymap name the first file defining it supplies it whole
(profiles are never merged key by key); names are listed in first-seen order
and sources records the supplying file of each profile."""
    files = _cott_normalize_f32_abi(files, CottList[ConfigFile], path="$.files")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/config/merge_config_files.py", "5922862c4d751bfa291bcee7b3f25e8720dfb8de077c478f99db74ab3be212e1", "merge_config_files", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.config.merge_config_files")
        _result = _implementation(files)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.config.merge_config_files"
        if _error.span is None:
            _error.span = {"end_byte":5453,"end_column":1,"end_line":151,"start_byte":4872,"start_column":1,"start_line":137}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.config.merge_config_files", phase="implementation-call", span={"end_byte":5453,"end_column":1,"end_line":151,"start_byte":4872,"start_column":1,"start_line":137}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.config.merge_config_files", phase="implementation-call", span={"end_byte":5453,"end_column":1,"end_line":151,"start_byte":4872,"start_column":1,"start_line":137}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, MergedConfig, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_unique_by((_result).profiles, "name")), "real.harlequin.config.merge_config_files", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.config.merge_config_files", clause="ensures:1", phase="ensures", span={"end_byte":5384,"end_column":53,"end_line":146,"start_byte":5336,"start_column":5,"start_line":146}, expected="true", actual="false")
        if not (_cott_contract_condition((_cott_unique_by((_result).keymaps, "name")), "real.harlequin.config.merge_config_files", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.config.merge_config_files", clause="ensures:2", phase="ensures", span={"end_byte":5435,"end_column":51,"end_line":147,"start_byte":5389,"start_column":5,"start_line":147}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, MergedConfig, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def select_profile(merged: MergedConfig, requested: Option[str]) -> Result[Option[Profile], ConfigError]:
    """Choose the profile an invocation uses. requested Some("None") (exact case)
means no profile: Ok(Nothing). requested Some(name) must be a profile of
merged; otherwise merged.default_profile when Some must be a profile of
merged; otherwise Ok(Nothing). A missing profile is Invalid with title
"Harlequin couldn't load your profile." and message "Could not load the
profile named {name} because it does not exist in any discovered config
files.". A broken default_profile is only an error when it is used."""
    merged = _cott_normalize_f32_abi(merged, MergedConfig, path="$.merged")
    requested = _cott_normalize_f32_abi(requested, Option[str], path="$.requested")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/config/select_profile.py", "d5bb54aba21b09df88fb768eff00cd87918b2dfce8a2cb37257e007353d88893", "select_profile", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.config.select_profile")
        _result = _implementation(merged, requested)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.config.select_profile"
        if _error.span is None:
            _error.span = {"end_byte":6209,"end_column":1,"end_line":171,"start_byte":5453,"start_column":1,"start_line":151}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.config.select_profile", phase="implementation-call", span={"end_byte":6209,"end_column":1,"end_line":171,"start_byte":5453,"start_column":1,"start_line":151}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.config.select_profile", phase="implementation-call", span={"end_byte":6209,"end_column":1,"end_line":171,"start_byte":5453,"start_column":1,"start_line":151}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Option[Profile], ConfigError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.config.select_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (ConfigError_Invalid,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.config.select_profile", phase="error", span={"end_byte":6209,"end_column":1,"end_line":171,"start_byte":5453,"start_column":1,"start_line":151}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.config.select_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.config.select_profile", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is ConfigError_Invalid:
            _cott_contract_condition(True, "real.harlequin.config.select_profile", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                selected = _cott_match_value.value
                return (_cott_contract_condition((True), "real.harlequin.config.select_profile", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.config.select_profile", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.config.select_profile", clause="ensures:1", phase="ensures", span={"end_byte":6160,"end_column":40,"end_line":165,"start_byte":6125,"start_column":5,"start_line":165}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Option[Profile], ConfigError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def interpolate_profile(profile: Profile, environment: FrozenMap[str, str], source: Option[str]) -> Result[Profile, ConfigError]:
    """Substitute environment variables in every Text value of profile, recursing
into Array and Table values (keys are never substituted). In a text,
"$${" is a literal "${" (not expanded further); "${NAME}" and
"${NAME:-DEFAULT}" where NAME matches [A-Za-z_][A-Za-z0-9_]* and DEFAULT is
any text without "}" are substitutions; everything else ("$HOME", "{HOME}",
"${not a var}", an unclosed "${X") stays as written. A variable that is
missing or set to "" is unset: its DEFAULT is used when written (possibly
empty), otherwise the result is Invalid with title "Harlequin couldn't load
your config file." and message "Config file reads the environment variable
{NAME}, which is not set. Set it, or write ${NAME:-a default} to say what to
use when it is not, at profiles.{profile}.{key}." followed, when source is
Some, by "\\nFound in the config file at {source}."; key is the dotted path
with "[i]" for array positions (for example
profiles.prod.conn_str[1])."""
    profile = _cott_normalize_f32_abi(profile, Profile, path="$.profile")
    environment = _cott_normalize_f32_abi(environment, FrozenMap[str, str], path="$.environment")
    source = _cott_normalize_f32_abi(source, Option[str], path="$.source")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/config/interpolate_profile.py", "aeb794d2ecc0b6f72f2cfc42b6ed23fcd7a3e51f10bc0ca894c2041ab7492c58", "interpolate_profile", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.config.interpolate_profile")
        _result = _implementation(profile, environment, source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.config.interpolate_profile"
        if _error.span is None:
            _error.span = {"end_byte":7541,"end_column":1,"end_line":199,"start_byte":6209,"start_column":1,"start_line":171}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.config.interpolate_profile", phase="implementation-call", span={"end_byte":7541,"end_column":1,"end_line":199,"start_byte":6209,"start_column":1,"start_line":171}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.config.interpolate_profile", phase="implementation-call", span={"end_byte":7541,"end_column":1,"end_line":199,"start_byte":6209,"start_column":1,"start_line":171}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Profile, ConfigError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.config.interpolate_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (ConfigError_Invalid,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.config.interpolate_profile", phase="error", span={"end_byte":7541,"end_column":1,"end_line":199,"start_byte":6209,"start_column":1,"start_line":171}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.config.interpolate_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.config.interpolate_profile", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is ConfigError_Invalid:
            _cott_contract_condition(True, "real.harlequin.config.interpolate_profile", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                resolved = _cott_match_value.value
                return (_cott_contract_condition(((((resolved).name == (profile).name) and (len((resolved).entries) == len((profile).entries)))), "real.harlequin.config.interpolate_profile", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.config.interpolate_profile", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.config.interpolate_profile", clause="ensures:1", phase="ensures", span={"end_byte":7492,"end_column":115,"end_line":193,"start_byte":7382,"start_column":5,"start_line":193}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Profile, ConfigError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def validate_config_file(file: ConfigFile, options_of: CottList[AdapterOptionSet], command_keys: CottList[str], builtin_keymaps: CottList[str]) -> CottList[ConfigProblem]:
    """Every problem in one read config file, without stopping at the first, the
way hsql --config validate reports them. options_of gives the declared
options of each adapter by adapter name; command_keys are the command-owned
profile keys. For each profile in file order: an adapter value that is not a
Text naming an adapter of options_of ("Profile sets adapter to '{value}',
which is not an installed adapter."); each key that is neither a command key
nor an option of the profile's adapter (duckdb when adapter is absent), in
sorted order ("Profile defines an option '{key}', which is not an option of
the {adapter} adapter." plus " Did you mean '{suggestion}'?" when
real.harlequin.sqltext.close_matches(key, both key sets, 1) finds one); each option value of
the wrong type (Flag needs Boolean, or the Text "true"/"false"; Repeated
needs an Array of Text; Choice needs one of its choices ignoring case; Text
and FilePath accept Text or a number) ("Profile sets {key} to a value the
{adapter} adapter cannot take: {reason}."). For each keymap whose name is a
builtin keymap name: "Keymap {name} is already defined by a plug-in; define
a new name and load both maps.". key is "profiles.{profile}.{key}" or
"keymaps.{name}". OptionKind and ConfigValue are closed variants:
narrow with isinstance(variant class) and read their declared fields
directly; do not use getattr, hasattr or any builtin reflection to
discover a variant payload. Iterate builtin_keymaps directly when
checking collisions; do not assign it to a local called builtins, which
the implementation audit reserves for Python reflection."""
    file = _cott_normalize_f32_abi(file, ConfigFile, path="$.file")
    options_of = _cott_normalize_f32_abi(options_of, CottList[AdapterOptionSet], path="$.options_of")
    command_keys = _cott_normalize_f32_abi(command_keys, CottList[str], path="$.command_keys")
    builtin_keymaps = _cott_normalize_f32_abi(builtin_keymaps, CottList[str], path="$.builtin_keymaps")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/config/validate_config_file.py", "f0f13a8e3d74c8fa7bdfbec87ca56704e2e9ba20d671b03ef0ae950f5ebfe6b6", "validate_config_file", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.config.validate_config_file")
        _result = _implementation(file, options_of, command_keys, builtin_keymaps)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.config.validate_config_file"
        if _error.span is None:
            _error.span = {"end_byte":9441,"end_column":1,"end_line":232,"start_byte":7541,"start_column":1,"start_line":199}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.config.validate_config_file", phase="implementation-call", span={"end_byte":9441,"end_column":1,"end_line":232,"start_byte":7541,"start_column":1,"start_line":199}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.config.validate_config_file", phase="implementation-call", span={"end_byte":9441,"end_column":1,"end_line":232,"start_byte":7541,"start_column":1,"start_line":199}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[ConfigProblem], path="$.return")
    _result = _cott_wrap_async_protocol(_result, CottList[ConfigProblem], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def write_profile(path: Path, profile: Profile, default_profile: Option[str]) -> Result[Path, ConfigError]:
    """Save profile into the config file at path with tomlkit, preserving comments,
formatting, other profiles and every unrelated table of the existing file.
The profile table profiles.{name} is replaced as a whole with the profile's
entries in order. default_profile Some(name) sets the top-level
default_profile; Nothing removes it. For a file named pyproject.toml the
changes go under [tool.harlequin] and the rest of the file is untouched. A
missing file and its parent directories are created. An existing file that
is not valid TOML is refused rather than overwritten: Invalid with title
"Harlequin could not load the config file." and the parse error. Other
failures are Invalid with title "Harlequin could not create your
configuration." and the OS error text. Returns path."""
    path = _cott_normalize_f32_abi(path, Path, path="$.path")
    profile = _cott_normalize_f32_abi(profile, Profile, path="$.profile")
    default_profile = _cott_normalize_f32_abi(default_profile, Option[str], path="$.default_profile")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/config/write_profile.py", "d8aa56860294859375a67ab44f3bf0429f68a3651b0ca352ff0fc87cefd3e13f", "write_profile", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.config.write_profile")
        _result = _implementation(path, profile, default_profile)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.config.write_profile"
        if _error.span is None:
            _error.span = {"end_byte":10674,"end_column":1,"end_line":264,"start_byte":9591,"start_column":1,"start_line":239}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.config.write_profile", phase="implementation-call", span={"end_byte":10674,"end_column":1,"end_line":264,"start_byte":9591,"start_column":1,"start_line":239}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.config.write_profile", phase="implementation-call", span={"end_byte":10674,"end_column":1,"end_line":264,"start_byte":9591,"start_column":1,"start_line":239}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Path, ConfigError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.config.write_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (ConfigError_Invalid,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.config.write_profile", phase="error", span={"end_byte":10674,"end_column":1,"end_line":264,"start_byte":9591,"start_column":1,"start_line":239}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.config.write_profile", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.config.write_profile", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is ConfigError_Invalid:
            _cott_contract_condition(True, "real.harlequin.config.write_profile", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                written = _cott_match_value.value
                return (_cott_contract_condition(((written == path)), "real.harlequin.config.write_profile", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.config.write_profile", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.config.write_profile", clause="ensures:1", phase="ensures", span={"end_byte":10604,"end_column":50,"end_line":258,"start_byte":10559,"start_column":5,"start_line":258}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Path, ConfigError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def write_keymap(path: Path, keymap: KeyMap) -> Result[Path, ConfigError]:
    """Save keymap into the config file at path as the array of tables
keymaps.{name}, each binding a table with keys, action and (when Some)
key_display, replacing any keymap of that name and preserving everything
else in the file exactly as write_profile does (including pyproject.toml's
[tool.harlequin] handling and parent creation). Errors as write_profile.
Returns path."""
    path = _cott_normalize_f32_abi(path, Path, path="$.path")
    keymap = _cott_normalize_f32_abi(keymap, KeyMap, path="$.keymap")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/config/write_keymap.py", "09cb2cb6ed021f9cbcae41580bd2bb35dec21752949a0beb1bd566ef6e19483b", "write_keymap", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.config.write_keymap")
        _result = _implementation(path, keymap)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.config.write_keymap"
        if _error.span is None:
            _error.span = {"end_byte":11282,"end_column":1,"end_line":280,"start_byte":10674,"start_column":1,"start_line":264}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.config.write_keymap", phase="implementation-call", span={"end_byte":11282,"end_column":1,"end_line":280,"start_byte":10674,"start_column":1,"start_line":264}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.config.write_keymap", phase="implementation-call", span={"end_byte":11282,"end_column":1,"end_line":280,"start_byte":10674,"start_column":1,"start_line":264}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[Path, ConfigError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.harlequin.config.write_keymap", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (ConfigError_Invalid,):
                raise CottContractViolation("returned error is not allowed", symbol="real.harlequin.config.write_keymap", phase="error", span={"end_byte":11282,"end_column":1,"end_line":280,"start_byte":10674,"start_column":1,"start_line":264}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.harlequin.config.write_keymap", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.harlequin.config.write_keymap", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is ConfigError_Invalid:
            _cott_contract_condition(True, "real.harlequin.config.write_keymap", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                written = _cott_match_value.value
                return (_cott_contract_condition(((written == path)), "real.harlequin.config.write_keymap", "ensures:1"))
            _cott_contract_condition((False), "real.harlequin.config.write_keymap", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.harlequin.config.write_keymap", clause="ensures:1", phase="ensures", span={"end_byte":11212,"end_column":50,"end_line":274,"start_byte":11167,"start_column":5,"start_line":274}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[Path, ConfigError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def profile_toml(profile: Profile, secret_keys: CottList[str]) -> str:
    """Render one profile as the body of a TOML table (key = value lines in entry
order, nested tables inline), masking values: an entry whose key is in
secret_keys or matches (case-insensitively) password, passwd, pwd, secret,
token, api[_-]?key, access[_-]?key or private[_-]?key is written as
"********" (an Array becomes an array of that many "********"); a conn_str
value is written with real.harlequin.sqltext.redact_connection_string
applied to each string."""
    profile = _cott_normalize_f32_abi(profile, Profile, path="$.profile")
    secret_keys = _cott_normalize_f32_abi(secret_keys, CottList[str], path="$.secret_keys")
    try:
        _implementation = _cott_load("_cott_impl/real/harlequin/config/profile_toml.py", "d6e5099acc6463e5711bce3c0d07b93bdcc8e79fcb3c18f1cffb0566e6c833b7", "profile_toml", expected_project_name="harlequin", expected_cott_symbol="real.harlequin.config.profile_toml")
        _result = _implementation(profile, secret_keys)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.harlequin.config.profile_toml"
        if _error.span is None:
            _error.span = {"end_byte":11871,"end_column":1,"end_line":293,"start_byte":11282,"start_column":1,"start_line":280}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.harlequin.config.profile_toml", phase="implementation-call", span={"end_byte":11871,"end_column":1,"end_line":293,"start_byte":11282,"start_column":1,"start_line":280}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.harlequin.config.profile_toml", phase="implementation-call", span={"end_byte":11871,"end_column":1,"end_line":293,"start_byte":11282,"start_column":1,"start_line":280}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["AdapterOptionSet", "ConfigEntry", "ConfigError", "ConfigError_Invalid", "ConfigFile", "ConfigProblem", "ConfigValue", "ConfigValue_Array", "ConfigValue_Boolean", "ConfigValue_Integer", "ConfigValue_Real", "ConfigValue_Table", "ConfigValue_Text", "MergedConfig", "Profile", "ProfileSource", "config_search_paths", "interpolate_profile", "merge_config_files", "profile_toml", "read_config_file", "select_profile", "validate_config_file", "write_keymap", "write_profile"]
