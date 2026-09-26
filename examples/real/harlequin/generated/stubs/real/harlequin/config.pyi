from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.config_types import AdapterOptionSet as AdapterOptionSet, ConfigEntry as ConfigEntry, ConfigError as ConfigError, ConfigError_Invalid as ConfigError_Invalid, ConfigFile as ConfigFile, ConfigProblem as ConfigProblem, ConfigValue as ConfigValue, ConfigValue_Array as ConfigValue_Array, ConfigValue_Boolean as ConfigValue_Boolean, ConfigValue_Integer as ConfigValue_Integer, ConfigValue_Real as ConfigValue_Real, ConfigValue_Table as ConfigValue_Table, ConfigValue_Text as ConfigValue_Text, MergedConfig as MergedConfig, Profile as Profile, ProfileSource as ProfileSource
from real.harlequin.adapters_types import AdapterOption
from real.harlequin.keymap_types import KeyMap
"""The config files Harlequin looks for, nearest (highest priority) first:
explicit when given; then cwd/harlequin.toml, cwd/.harlequin.toml,
cwd/pyproject.toml; then user_config_dir/harlequin.toml,
user_config_dir/.harlequin.toml, user_config_dir/config.toml; then
home/harlequin.toml, home/.harlequin.toml, home/pyproject.toml. No
deduplication is performed."""
def config_search_paths(explicit: Option[Path], cwd: Path, user_config_dir: Path, home: Path) -> CottList[Path]: ...

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
def read_config_file(path: Path) -> Result[Option[ConfigFile], ConfigError]: ...

"""Merge files given nearest first, as MergedConfig documents: the first
non-Nothing default_profile wins (with its file as default_source); for every
profile name and keymap name the first file defining it supplies it whole
(profiles are never merged key by key); names are listed in first-seen order
and sources records the supplying file of each profile."""
def merge_config_files(files: CottList[ConfigFile]) -> MergedConfig: ...

"""Choose the profile an invocation uses. requested Some("None") (exact case)
means no profile: Ok(Nothing). requested Some(name) must be a profile of
merged; otherwise merged.default_profile when Some must be a profile of
merged; otherwise Ok(Nothing). A missing profile is Invalid with title
"Harlequin couldn't load your profile." and message "Could not load the
profile named {name} because it does not exist in any discovered config
files.". A broken default_profile is only an error when it is used."""
def select_profile(merged: MergedConfig, requested: Option[str]) -> Result[Option[Profile], ConfigError]: ...

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
def interpolate_profile(profile: Profile, environment: FrozenMap[str, str], source: Option[str]) -> Result[Profile, ConfigError]: ...

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
def validate_config_file(file: ConfigFile, options_of: CottList[AdapterOptionSet], command_keys: CottList[str], builtin_keymaps: CottList[str]) -> CottList[ConfigProblem]: ...

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
def write_profile(path: Path, profile: Profile, default_profile: Option[str]) -> Result[Path, ConfigError]: ...

"""Save keymap into the config file at path as the array of tables
keymaps.{name}, each binding a table with keys, action and (when Some)
key_display, replacing any keymap of that name and preserving everything
else in the file exactly as write_profile does (including pyproject.toml's
[tool.harlequin] handling and parent creation). Errors as write_profile.
Returns path."""
def write_keymap(path: Path, keymap: KeyMap) -> Result[Path, ConfigError]: ...

"""Render one profile as the body of a TOML table (key = value lines in entry
order, nested tables inline), masking values: an entry whose key is in
secret_keys or matches (case-insensitively) password, passwd, pwd, secret,
token, api[_-]?key, access[_-]?key or private[_-]?key is written as
"********" (an Array becomes an array of that many "********"); a conn_str
value is written with real.harlequin.sqltext.redact_connection_string
applied to each string."""
def profile_toml(profile: Profile, secret_keys: CottList[str]) -> str: ...

__all__ = ["AdapterOptionSet", "ConfigEntry", "ConfigError", "ConfigError_Invalid", "ConfigFile", "ConfigProblem", "ConfigValue", "ConfigValue_Array", "ConfigValue_Boolean", "ConfigValue_Integer", "ConfigValue_Real", "ConfigValue_Table", "ConfigValue_Text", "MergedConfig", "Profile", "ProfileSource", "config_search_paths", "interpolate_profile", "merge_config_files", "profile_toml", "read_config_file", "select_profile", "validate_config_file", "write_keymap", "write_profile"]
