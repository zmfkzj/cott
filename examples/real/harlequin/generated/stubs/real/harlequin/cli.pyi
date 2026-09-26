from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.harlequin.cli_types import CliArguments as CliArguments, CliError as CliError, CliError_Usage as CliError_Usage, FirstPass as FirstPass, HARLEQUIN_VERSION as HARLEQUIN_VERSION, HarlequinSettings as HarlequinSettings, SshSettings as SshSettings
from real.harlequin.adapters_types import AdapterDescriptor, AdapterKind, AdapterOption, ConnectionRequest
from real.harlequin.config_types import ConfigEntry, ConfigError, ConfigError_Invalid, Profile
"""Scan raw arguments (without the program name) up to a "--": -a NAME,
-aNAME, --adapter NAME and --adapter=NAME set adapter (last wins, lower
cased); -P NAME, -PNAME, --profile NAME and --profile=NAME set profile;
--config-path PATH and --config-path=PATH set config_path; --help,
--version, --config and --keys set the corresponding wants flags. A value
option at the very end without a value sets nothing. Nothing else is
interpreted."""
def first_pass(arguments: CottList[str]) -> FirstPass: ...

"""The profile keys the harlequin command itself owns, in this order: adapter,
conn_str, keymap_name, limit, locale, no_download_tzdata, no_write_history,
output, read_only, show_files, show_s3, ssh_allow_reuse, ssh_batch_mode,
ssh_forward, ssh_host, ssh_timeout, theme, viewer_max_rows."""
def harlequin_option_names() -> CottList[str]: ...

"""Parse the harlequin command line like Harlequin's click command.
Core options (spellings | profile key | kind):
-P/--profile TEXT (not a profile key: sets profile) ;
--config-path PATH (sets config_path) ; -t/--theme TEXT | theme | Text ;
--viewer-max-rows INTEGER | viewer_max_rows | Integer, must be >= -1 ;
--limit INTEGER | limit | Integer, >= -1 ; -o/--output PATH | output | Text ;
-a/--adapter NAME | adapter | Text, must be one of adapter_names ignoring case
(stored lower case) ; --no-write-history | no_write_history | flag ;
-r/--read-only | read_only | flag ; -f/--show-files DIRECTORY | show_files |
Text ; --show-s3/--s3 TEXT | show_s3 | Text ; --keymap-name TEXT (repeatable)
| keymap_name | Array ; --ssh-host TEXT | ssh_host | Text ; --ssh-forward TEXT
(repeatable) | ssh_forward | Array ; --ssh-batch-mode | ssh_batch_mode | flag ;
--ssh-allow-reuse | ssh_allow_reuse | flag ; --ssh-timeout FLOAT |
ssh_timeout | Real, must be > 0 ; --locale TEXT | locale | Text ;
--no-download-tzdata | no_download_tzdata | flag ; --config (run the config
wizard) ; --keys (run the keymap editor) ; --version ; --help.
Flags are stored as Boolean true. adapter_options adds each option of the
selected adapter as --{name} plus its short_decls, stored under the name with
"-" replaced by "_": Flag as Boolean true, Repeated as an Array of Text,
Choice as the matching choice's declared spelling (case-insensitive match),
Text and FilePath as Text.
Grammar: options and positional arguments may interleave; "--" ends options
and every later argument is positional; a lone "-" is positional. A long
option takes its value from "--name=VALUE" or the next argument (taken
verbatim even when it starts with "-"); a flag written "--flag=VALUE" is an
error. A short option taking a value accepts "-xVALUE" or the next argument;
short flags may be clustered ("-r"). Positional arguments collect into
conn_str.
Errors are Usage(message) for the first offending argument, with click's
wording: "No such option: {arg}" (for spellings that belong only to hsql:
-c, --command, --file, --format, --csv, --json, --jsonl, --markdown, -x,
--vertical, --tuples-only, -A, --no-align, --no-header, --no-footer,
--null-string, --timeout, --catalog, --catalog-search, --path, --history,
--history-search, --spec, --info, --skill, --display-rows, --result,
--on-error, --stats, --color, --serve, --session, --session-reset,
--session-status, --queue-timeout, --idle-timeout and --max-lifetime, instead "{arg} is not a
harlequin option. Did you mean 'hsql {arg}'? hsql is Harlequin's headless
CLI: it runs SQL and exits. See https://harlequin.sh/docs/headless");
"Option '{name}' requires an argument."; "Option '{name}' does not take a
value."; "Invalid value for '{names}': '{value}' is not one of {choices}."
(choices quoted with ' and joined by ", "); "Invalid value for '{names}':
'{value}' is not a valid integer." / "is not a valid float."; "Invalid value
for '{names}': {value} is not in the range x>=-1." (x>0 for --ssh-timeout);
where names is the option's spellings joined by " / " as click lists them
(for example "'-a' / '--adapter'" written as '--adapter' / '-a')."""
def parse_harlequin_arguments(arguments: CottList[str], adapter_names: CottList[str], adapter_options: CottList[AdapterOption]) -> Result[CliArguments, CliError]: ...

"""The --version output: "harlequin, version {HARLEQUIN_VERSION}\\n\\nInstalled
Adapters:\\n" followed by one line "  - {name}, version {HARLEQUIN_VERSION}\\n"
per adapter name in sorted order (every adapter ships in this build)."""
def harlequin_version_text(adapter_names: CottList[str]) -> str: ...

"""The --help text, in click's layout: "Usage: harlequin [OPTIONS] [CONN_STR]...",
a blank line, the indented description "  The Harlequin IDE: a SQL IDE for
your terminal. CONN_STR is zero or more connection strings or database file
paths for the selected adapter.", then an "Options:" section with one entry
per core option of parse_harlequin_arguments (spellings, metavar, and a help
sentence naming its default), then for each descriptor in order a section
"{display_name} Adapter Options:" listing each option of
real.harlequin.adapters.adapter_options(kind) as its spellings, metavar
(TEXT, PATH or [choice|...] ; flags have none) and description, with secret
options noted "(secret)". Entries are two-space indented with help text
aligned in a column and wrapped at 79 characters."""
def harlequin_help(descriptors: CottList[AdapterDescriptor]) -> str: ...

"""Combine the selected (already interpolated) profile with the command line
the way Harlequin does, for the adapter descriptor (the adapter typed with
-a, else the profile's adapter, else duckdb) whose options are options.
Start from the profile's entries; every explicit command-line entry
replaces the profile entry of the same key (explicit false and 0 included);
a nonempty positional conn_str replaces the profile's conn_str (a profile
conn_str may be one Text or an Array of Text). Then read the keys:
adapter (must name descriptor), conn_str, read_only (Boolean, or the Text
"true"/"false"), theme (Text, default "harlequin"), keymap_name (Text or
Array of Text, default ["vscode"]), limit (whole number >= -1; -1 means
Nothing; 0 is zero rows; default Nothing), viewer_max_rows (whole number >= -1;
0 and -1 mean Nothing; default 100000), output, show_files, show_s3, locale
(Text), no_write_history and no_download_tzdata (Boolean only),
ssh_host, ssh_forward (Array of Text or one Text), ssh_batch_mode (Boolean),
ssh_allow_reuse (Boolean; true is refused when it came from the profile),
ssh_timeout (number > 0; default 60.0). Every other key must be an option of
options (by profile spelling) and becomes an AdapterSetting: Flag options take
Boolean or "true"/"false" Text; Repeated options take an Array of Text (a
single Text becomes a one-element list); Choice options take one of choices
ignoring case, normalized; Text and FilePath options take Text, numbers
becoming their text.
Errors are Invalid(title, message) with title "Harlequin couldn't load your
config file." and messages: "Profile defines an option '{key}', which is not
an option of the {adapter} adapter." (plus " Did you mean '{match}'?" when
real.harlequin.sqltext.close_matches(key, command and adapter keys, 1)
finds one);
"Profile sets {key} to a value the {adapter} adapter cannot take: {reason}.";
"{key}={value!r} is not a whole number of rows."; "{key}={value!r} is not a
number of rows. Pass -1 for no limit."; "{key}={value!r} is not a positive
number of seconds. Leave it out for a run that takes as long as it takes.";
"no_write_history must be true or false."; "ssh_allow_reuse can only be set
on the command line. Pass --ssh-allow-reuse."; "SSH options are set but
ssh_host is not."; and, when read_only is true for an adapter that does not
implement read-only, title "Harlequin could not start." and message
"{adapter} does not declare read-only support, so --read-only cannot be
honored. See `hsql --info`."."""
def resolve_harlequin_settings(profile: Option[Profile], arguments: CliArguments, descriptor: AdapterDescriptor, options: CottList[AdapterOption]) -> Result[HarlequinSettings, ConfigError]: ...

__all__ = ["CliArguments", "CliError", "CliError_Usage", "FirstPass", "HARLEQUIN_VERSION", "HarlequinSettings", "SshSettings", "first_pass", "harlequin_help", "harlequin_option_names", "harlequin_version_text", "parse_harlequin_arguments", "resolve_harlequin_settings"]
