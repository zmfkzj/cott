from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.harlequin.adapters_types import AdapterDescriptor, AdapterOption, AdapterSetting
from real.harlequin.config_types import ConfigEntry, Profile
from real.harlequin.keymap_types import KeyMap

"""One row of the keymap editor's table: the action name, its title as the
table shows it ("{Scope}: {Description}", for example "Code Editor: Run
Query"), the keys bound to it (unique, sorted), and the key display override."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class KeyRow:
    __hash__ = None
    action: str
    title: str
    keys: CottList[str]
    key_display: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "action", _cott_validate_abi(self.action, str, path="$.action"))
        if not _cott_validated_construction():
            object.__setattr__(self, "title", _cott_validate_abi(self.title, str, path="$.title"))
        if not _cott_validated_construction():
            object.__setattr__(self, "keys", _cott_validate_abi(self.keys, CottList[str], path="$.keys"))
        if not _cott_validated_construction():
            object.__setattr__(self, "key_display", _cott_validate_abi(self.key_display, Option[str], path="$.key_display"))

"""The answers the config wizard collected, as the user typed them (blank
strings for skipped text questions). conn_str, ssh_forwards and Repeated
adapter options are space-separated text. options holds only the adapter
options the user chose to set, with SettingValue.Text for text/path/choice
answers, Flag for flags and Values for repeated options."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class WizardAnswers:
    __hash__ = None
    profile_name: str
    adapter: str
    conn_str: str
    read_only: bool
    theme: str
    keymap_names: CottList[str]
    limit: str
    viewer_max_rows: str
    show_files: str
    show_s3: str
    locale: str
    use_ssh: bool
    ssh_host: str
    ssh_forwards: str
    ssh_batch_mode: bool
    ssh_timeout: str
    options: CottList[AdapterSetting]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "profile_name", _cott_validate_abi(self.profile_name, str, path="$.profile_name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "adapter", _cott_validate_abi(self.adapter, str, path="$.adapter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "conn_str", _cott_validate_abi(self.conn_str, str, path="$.conn_str"))
        if not _cott_validated_construction():
            object.__setattr__(self, "read_only", _cott_validate_abi(self.read_only, bool, path="$.read_only"))
        if not _cott_validated_construction():
            object.__setattr__(self, "theme", _cott_validate_abi(self.theme, str, path="$.theme"))
        if not _cott_validated_construction():
            object.__setattr__(self, "keymap_names", _cott_validate_abi(self.keymap_names, CottList[str], path="$.keymap_names"))
        if not _cott_validated_construction():
            object.__setattr__(self, "limit", _cott_validate_abi(self.limit, str, path="$.limit"))
        if not _cott_validated_construction():
            object.__setattr__(self, "viewer_max_rows", _cott_validate_abi(self.viewer_max_rows, str, path="$.viewer_max_rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "show_files", _cott_validate_abi(self.show_files, str, path="$.show_files"))
        if not _cott_validated_construction():
            object.__setattr__(self, "show_s3", _cott_validate_abi(self.show_s3, str, path="$.show_s3"))
        if not _cott_validated_construction():
            object.__setattr__(self, "locale", _cott_validate_abi(self.locale, str, path="$.locale"))
        if not _cott_validated_construction():
            object.__setattr__(self, "use_ssh", _cott_validate_abi(self.use_ssh, bool, path="$.use_ssh"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ssh_host", _cott_validate_abi(self.ssh_host, str, path="$.ssh_host"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ssh_forwards", _cott_validate_abi(self.ssh_forwards, str, path="$.ssh_forwards"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ssh_batch_mode", _cott_validate_abi(self.ssh_batch_mode, bool, path="$.ssh_batch_mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ssh_timeout", _cott_validate_abi(self.ssh_timeout, str, path="$.ssh_timeout"))
        if not _cott_validated_construction():
            object.__setattr__(self, "options", _cott_validate_abi(self.options, CottList[AdapterSetting], path="$.options"))

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
"""The row after the binding editor's Submit: keys made unique and sorted
(empty strings dropped), key_display Nothing when blank, else the text."""
"""The keymap the editor saves: named name, with one KeyBinding per row whose
keys are nonempty or whose key_display is set, in row order; keys joined
with "," and key_display copied."""
"""The keymap-name validator of the save dialog: Some("Cannot use the name of
an existing keymap plug-in") when name equals a builtin keymap name, Some(
"Cannot be empty") when name is blank, else Nothing."""
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
__all__ = ["KeyRow", "WizardAnswers"]
