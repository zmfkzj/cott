from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.harlequin.adapters_types import AdapterOption
from real.harlequin.keymap_types import KeyMap

"""A TOML value as Harlequin's config files hold it. Array elements and Table
entries keep file order."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigValue_Text:
    __hash__ = None
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigValue_Integer:
    __hash__ = None
    value: I64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigValue_Real:
    __hash__ = None
    value: F64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigValue_Boolean:
    __hash__ = None
    value: bool

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigValue_Array:
    __hash__ = None
    values: CottList[ConfigValue]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigValue_Table:
    __hash__ = None
    entries: CottList[ConfigEntry]

ConfigValue: TypeAlias = Union[ConfigValue_Text, ConfigValue_Integer, ConfigValue_Real, ConfigValue_Boolean, ConfigValue_Array, ConfigValue_Table]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigEntry:
    __hash__ = None
    key: str
    value: ConfigValue

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "key", _cott_validate_abi(self.key, str, path="$.key"))
        if not _cott_validated_construction():
            object.__setattr__(self, "value", _cott_validate_abi(self.value, ConfigValue, path="$.value"))

"""One profile: its name and its keys in file order (profile keys are command
options such as adapter, conn_str, theme, limit, keymap_name, and adapter
options such as init_path)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Profile:
    __hash__ = None
    name: str
    entries: CottList[ConfigEntry]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "entries", _cott_validate_abi(self.entries, CottList[ConfigEntry], path="$.entries"))

"""One config file after reading; path is the file's path as text. For a
pyproject.toml only its [tool.harlequin]
table counts. defines_anything is false for a file (or pyproject section)
that defines no default_profile, profile or keymap."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigFile:
    __hash__ = None
    path: str
    default_profile: Option[str]
    profiles: CottList[Profile]
    keymaps: CottList[KeyMap]
    defines_anything: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, str, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "default_profile", _cott_validate_abi(self.default_profile, Option[str], path="$.default_profile"))
        if not _cott_validated_construction():
            object.__setattr__(self, "profiles", _cott_validate_abi(self.profiles, CottList[Profile], path="$.profiles"))
        if not _cott_validated_construction():
            object.__setattr__(self, "keymaps", _cott_validate_abi(self.keymaps, CottList[KeyMap], path="$.keymaps"))
        if not _cott_validated_construction():
            object.__setattr__(self, "defines_anything", _cott_validate_abi(self.defines_anything, bool, path="$.defines_anything"))

"""Several config files merged nearest-first: default_profile comes from the
first file that sets one; each profile name and keymap name is supplied whole
by the first file that defines it. sources pairs each profile name with the
file that supplied it, and default_source is the file that supplied
default_profile."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MergedConfig:
    __hash__ = None
    default_profile: Option[str]
    default_source: Option[str]
    profiles: CottList[Profile]
    keymaps: CottList[KeyMap]
    sources: CottList[ProfileSource]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "default_profile", _cott_validate_abi(self.default_profile, Option[str], path="$.default_profile"))
        if not _cott_validated_construction():
            object.__setattr__(self, "default_source", _cott_validate_abi(self.default_source, Option[str], path="$.default_source"))
        if not _cott_validated_construction():
            object.__setattr__(self, "profiles", _cott_validate_abi(self.profiles, CottList[Profile], path="$.profiles"))
        if not _cott_validated_construction():
            object.__setattr__(self, "keymaps", _cott_validate_abi(self.keymaps, CottList[KeyMap], path="$.keymaps"))
        if not _cott_validated_construction():
            object.__setattr__(self, "sources", _cott_validate_abi(self.sources, CottList[ProfileSource], path="$.sources"))

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ProfileSource:
    __hash__ = None
    name: str
    path: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, str, path="$.path"))

"""A configuration error as Harlequin reports it: a panel title and the message.
The command exits with status 2."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigError_Invalid:
    __hash__ = None
    title: str
    message: str

ConfigError: TypeAlias = Union[ConfigError_Invalid]

"""One problem found by validate_config_file: the file, the dotted key it is at
(Nothing for a file-level problem) and the message."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigProblem:
    __hash__ = None
    path: str
    key: Option[str]
    message: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, str, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "key", _cott_validate_abi(self.key, Option[str], path="$.key"))
        if not _cott_validated_construction():
            object.__setattr__(self, "message", _cott_validate_abi(self.message, str, path="$.message"))

"""The config files Harlequin looks for, nearest (highest priority) first:
explicit when given; then cwd/harlequin.toml, cwd/.harlequin.toml,
cwd/pyproject.toml; then user_config_dir/harlequin.toml,
user_config_dir/.harlequin.toml, user_config_dir/config.toml; then
home/harlequin.toml, home/.harlequin.toml, home/pyproject.toml. No
deduplication is performed."""
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
"""Merge files given nearest first, as MergedConfig documents: the first
non-Nothing default_profile wins (with its file as default_source); for every
profile name and keymap name the first file defining it supplies it whole
(profiles are never merged key by key); names are listed in first-seen order
and sources records the supplying file of each profile."""
"""Choose the profile an invocation uses. requested Some("None") (exact case)
means no profile: Ok(Nothing). requested Some(name) must be a profile of
merged; otherwise merged.default_profile when Some must be a profile of
merged; otherwise Ok(Nothing). A missing profile is Invalid with title
"Harlequin couldn't load your profile." and message "Could not load the
profile named {name} because it does not exist in any discovered config
files.". A broken default_profile is only an error when it is used."""
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
"""The declared options of one adapter, by its entry-point name."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterOptionSet:
    __hash__ = None
    adapter: str
    options: CottList[AdapterOption]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "adapter", _cott_validate_abi(self.adapter, str, path="$.adapter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "options", _cott_validate_abi(self.options, CottList[AdapterOption], path="$.options"))

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
"""Save keymap into the config file at path as the array of tables
keymaps.{name}, each binding a table with keys, action and (when Some)
key_display, replacing any keymap of that name and preserving everything
else in the file exactly as write_profile does (including pyproject.toml's
[tool.harlequin] handling and parent creation). Errors as write_profile.
Returns path."""
"""Render one profile as the body of a TOML table (key = value lines in entry
order, nested tables inline), masking values: an entry whose key is in
secret_keys or matches (case-insensitively) password, passwd, pwd, secret,
token, api[_-]?key, access[_-]?key or private[_-]?key is written as
"********" (an Array becomes an array of that many "********"); a conn_str
value is written with real.harlequin.sqltext.redact_connection_string
applied to each string."""
__all__ = ["AdapterOptionSet", "ConfigEntry", "ConfigError", "ConfigError_Invalid", "ConfigFile", "ConfigProblem", "ConfigValue", "ConfigValue_Array", "ConfigValue_Boolean", "ConfigValue_Integer", "ConfigValue_Real", "ConfigValue_Table", "ConfigValue_Text", "MergedConfig", "Profile", "ProfileSource"]
