from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
PGCLI_DEFAULT_CONFIG: Final[str] = "# vi: ft=dosini\n[main]\n\n# Enables context sensitive auto-completion. If this is disabled, all\n# possible completions will be listed.\nsmart_completion = True\n\n# Enable auto suggestions (like Fish shell).\nauto_suggest = True\n\n# Display the completions in several columns. (More completions will be\n# visible.)\nwider_completion_menu = False\n\n# Do not create new connections for refreshing completions; Equivalent to\n# always running with the --single-connection flag.\nalways_use_single_connection = False\n\n# Multi-line mode allows breaking up the sql statements into multiple lines. If\n# this is set to True, then the end of the statements must have a semi-colon.\n# If this is set to False then sql statements can't be split into multiple\n# lines. End of line (return) is considered as the end of the statement.\nmulti_line = False\n\n# If multi_line_mode is set to \"psql\", in multi-line mode, [Enter] will execute\n# the current input if the input ends in a semicolon.\n# If multi_line_mode is set to \"safe\", in multi-line mode, [Enter] will always\n# insert a newline, and [Esc] [Enter] or [Alt]-[Enter] must be used to execute\n# a command.\nmulti_line_mode = psql\n\n# Destructive warning will alert you before executing a sql statement\n# that may cause harm to the database such as \"drop table\", \"drop database\",\n# \"shutdown\", \"delete\", or \"update\".\n# You can pass a list of destructive commands or leave it empty if you want to skip all warnings.\n# \"unconditional_update\" will warn you of update statements that don't have a where clause\ndestructive_warning = drop, shutdown, delete, truncate, alter, update, unconditional_update\n\n# When `destructive_warning` is on and the user declines to proceed with a\n# destructive statement, the current transaction (if any) is left untouched,\n# by default. When setting `destructive_warning_restarts_connection` to\n# \"True\", the connection to the server is restarted. In that case, the\n# transaction (if any) is rolled back.\ndestructive_warning_restarts_connection = False\n\n# When this option is on (and if `destructive_warning` is not empty),\n# destructive statements are not executed when outside of a transaction.\ndestructive_statements_require_transaction = False\n\n# Enables expand mode, which is similar to `\\x` in psql.\nexpand = False\n\n# Enables auto expand mode, which is similar to `\\x auto` in psql.\nauto_expand = False\n\n# Auto-retry queries on connection failures and other operational errors. If\n# False, will prompt to rerun the failed query instead of auto-retrying.\nauto_retry_closed_connection = True\n\n# If set to True, table suggestions will include a table alias\ngenerate_aliases = False\n\n# Path to a json file that specifies specific table aliases to use when generate_aliases is set to True\n# the format for this file should be:\n# {\n#     \"some_table_name\": \"desired_alias\",\n#     \"some_other_table_name\": \"another_alias\"\n# }\nalias_map_file =\n\n# log_file location.\n# In Unix/Linux: ~/.config/pgcli/log\n# In Windows: %USERPROFILE%\\AppData\\Local\\dbcli\\pgcli\\log\n# %USERPROFILE% is typically C:\\Users\\{username}\nlog_file = default\n\n# keyword casing preference. Possible values: \"lower\", \"upper\", \"auto\"\nkeyword_casing = auto\n\n# casing_file location.\n# In Unix/Linux: ~/.config/pgcli/casing\n# In Windows: %USERPROFILE%\\AppData\\Local\\dbcli\\pgcli\\casing\n# %USERPROFILE% is typically C:\\Users\\{username}\ncasing_file = default\n\n# If generate_casing_file is set to True and there is no file in the above\n# location, one will be generated based on usage in SQL/PLPGSQL functions.\ngenerate_casing_file = False\n\n# Casing of column headers based on the casing_file described above\ncase_column_headers = True\n\n# history_file location.\n# In Unix/Linux: ~/.config/pgcli/history\n# In Windows: %USERPROFILE%\\AppData\\Local\\dbcli\\pgcli\\history\n# %USERPROFILE% is typically C:\\Users\\{username}\nhistory_file = default\n\n# Default log level. Possible values: \"CRITICAL\", \"ERROR\", \"WARNING\", \"INFO\"\n# and \"DEBUG\". \"NONE\" disables logging.\nlog_level = INFO\n\n# Order of columns when expanding * to column list\n# Possible values: \"table_order\" and \"alphabetic\"\nasterisk_column_order = table_order\n\n# Whether to qualify with table alias/name when suggesting columns\n# Possible values: \"always\", \"never\" and \"if_more_than_one_table\"\nqualify_columns = if_more_than_one_table\n\n# When no schema is entered, only suggest objects in search_path\nsearch_path_filter = False\n\n# Default pager. See https://www.pgcli.com/pager for more information on settings.\n# By default 'PAGER' environment variable is used. If the pager is less, and the 'LESS'\n# environment variable is not set, then LESS='-SRXF' will be automatically set.\n# pager = less\n\n# Timing of sql statements and table rendering.\ntiming = True\n\n# Hide the query text when executing named queries (\\n <name>).\n# Only the query results will be displayed.\n# Can be toggled at runtime with \\nq command.\nhide_named_query_text = False\n\n# Show/hide the informational toolbar with function keymap at the footer.\nshow_bottom_toolbar = True\n\n# Table format. Possible values: psql, plain, simple, grid, fancy_grid, pipe,\n# ascii, double, github, orgtbl, rst, mediawiki, html, latex, latex_booktabs,\n# textile, moinmoin, jira, vertical, tsv, csv, sql-insert, sql-update,\n# sql-update-1, sql-update-2 (formatter with sql-* prefix can format query\n# output to executable insertion or updating sql).\n# Recommended: psql, fancy_grid and grid.\ntable_format = psql\n\n# Syntax Style. Possible values: manni, igor, xcode, vim, autumn, vs, rrt,\n# native, perldoc, borland, tango, emacs, friendly, monokai, paraiso-dark,\n# colorful, murphy, bw, pastie, paraiso-light, trac, default, fruity\nsyntax_style = default\n\n# Keybindings:\n# When Vi mode is enabled you can use modal editing features offered by Vi in the REPL.\n# When Vi mode is disabled emacs keybindings such as Ctrl-A for home and Ctrl-E\n# for end are available in the REPL.\nvi = False\n\n# Seconds to wait for a connection before giving up. Only applies when nothing\n# else specifies a timeout: an explicit --timeout on the command line wins, then\n# a connect_timeout in the connection string, then $PGCONNECT_TIMEOUT. Use 0 to\n# wait forever, which is libpq's own default (the OS then gives up on the TCP\n# connection after a few minutes).\nconnect_timeout = 30\n\n# Error handling\n# When one of multiple SQL statements causes an error, choose to either\n# continue executing the remaining statements, or stopping\n# Possible values \"STOP\" or \"RESUME\"\non_error = STOP\n\n# Set threshold for row limit. Use 0 to disable limiting.\nrow_limit = 1000\n\n# Truncate long text fields to this value for tabular display (does not apply to csv).\n# Leave unset to disable truncation. Example: \"max_field_width = \"\n# Be aware that formatting might get slow with values larger than 500 and tables with\n# lots of records.\nmax_field_width = 500\n\n# Skip intro on startup and goodbye on exit\nless_chatty = False\n\n# Show all Postgres error fields (as listed in\n# https://www.postgresql.org/docs/current/protocol-error-fields.html).\n# Can be toggled with \\v.\nverbose_errors = False\n\n# Postgres prompt\n# \\t - Current date and time\n# \\u - Username\n# \\h - Short hostname of the server (up to first '.')\n# \\H - Hostname of the server\n# \\d - Database name\n# \\p - Database port\n# \\i - Postgres PID\n# \\# - \"@\" sign if logged in as superuser, '>' in other case\n# \\n - Newline\n# \\T - Transaction status: '*' if in a valid transaction, '!' if in a failed transaction, '?' if disconnected, empty otherwise\n# \\dsn_alias - name of dsn connection string alias if -D option is used (empty otherwise)\n# \\x1b[...m - insert ANSI escape sequence\n# eg: prompt = '\\x1b[35m\\u@\\x1b[32m\\h:\\x1b[36m\\d>'\nprompt = '\\u@\\h:\\d> '\n\n# Number of lines to reserve for the suggestion menu\nmin_num_menu_lines = 4\n\n# Character used to left pad multi-line queries to match the prompt size.\nmultiline_continuation_char = ''\n\n# The string used in place of a null value.\nnull_string = '<null>'\n\n# manage pager on startup\nenable_pager = True\n\n# Use keyring to automatically save and load password in a secure manner\nkeyring = True\n\n# Automatically set the session time zone to the local time zone\n# If unset, uses the server's time zone, which is the Postgres default\nuse_local_timezone = True\n\n# Custom colors for the completion menu, toolbar, etc.\n[colors]\ncompletion-menu.completion.current = 'bg:#ffffff #000000'\ncompletion-menu.completion = 'bg:#008888 #ffffff'\ncompletion-menu.meta.completion.current = 'bg:#44aaaa #000000'\ncompletion-menu.meta.completion = 'bg:#448888 #ffffff'\ncompletion-menu.multi-column-meta = 'bg:#aaffff #000000'\nscrollbar.arrow = 'bg:#003333'\nscrollbar = 'bg:#00aaaa'\nselected = '#ffffff bg:#6666aa'\nsearch = '#ffffff bg:#4444aa'\nsearch.current = '#ffffff bg:#44aa44'\nbottom-toolbar = 'bg:#222222 #aaaaaa'\nbottom-toolbar.off = 'bg:#222222 #888888'\nbottom-toolbar.on = 'bg:#222222 #ffffff'\nsearch-toolbar = 'noinherit bold'\nsearch-toolbar.text = 'nobold'\nsystem-toolbar = 'noinherit bold'\narg-toolbar = 'noinherit bold'\narg-toolbar.text = 'nobold'\nbottom-toolbar.transaction.valid = 'bg:#222222 #00ff5f bold'\nbottom-toolbar.transaction.failed = 'bg:#222222 #ff005f bold'\n# These three values can be used to further refine the syntax highlighting.\n# They are commented out by default, since they have priority over the theme set\n# with the `syntax_style` setting and overriding its behavior can be confusing.\n# literal.string = '#ba2121'\n# literal.number = '#666666'\n# keyword = 'bold #008000'\n\n# style classes for colored table output\noutput.header = \"#00ff5f bold\"\noutput.odd-row = \"\"\noutput.even-row = \"\"\noutput.null = \"#808080\"\n\n# Named queries are queries you can execute by name.\n[named queries]\n# ver = \"SELECT version()\"\n\n# Here's where you can provide a list of connection string aliases.\n# You can use it by passing the -D option. `pgcli -D example_dsn`\n[alias_dsn]\n# example_dsn = postgresql://[user[:password]@][netloc][:port][/dbname]\n\n# Initial commands to execute when connecting to any database.\n[init-commands]\n# example = \"SET search_path TO myschema\"\n\n# Initial commands to execute when connecting to a DSN alias.\n[alias_dsn.init-commands]\n# example_dsn = \"SET search_path TO otherschema; SET timezone TO 'UTC'\"\n\n# Format for number representation\n# for decimal \"d\" - 12345678, \",d\" - 12,345,678\n# for float \"g\" - 123456.78, \",g\" - 123,456.78\n[data_formats]\ndecimal = \"\"\nfloat = \"\"\n\n# Per column formats for date/timestamp columns\n[column_date_formats]\n# use strftime format, e.g.\n# created = \"%Y-%m-%d\"\n\n# Per host ssh tunnel configuration\n[ssh tunnels]\n# ^example.*\\.host$ = myuser:mypasswd@my.tunnel.com:4000\n# .*\\.net = another.tunnel.com\n\n# Per dsn_alias ssh tunnel configuration\n[dsn ssh tunnels]\n# ^example_dsn$  = myuser:mypasswd@my.tunnel.com:4000\n"

"""Configuration failures. message is the text of the underlying error: the
configobj parse error message (for example "Invalid line ('abc') (matched as
neither section nor keyword) at line 3."), the configobj conversion message
(for example 'Value "maybe" is neither True nor False'), Python's int()
message (for example "invalid literal for int() with base 10: 'x'"), or the
str() of an OSError."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigError_Unreadable:
    __hash__ = None
    path: str
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigError_Invalid:
    __hash__ = None
    message: str

ConfigError: TypeAlias = Union[ConfigError_Unreadable, ConfigError_Invalid]

"""One key of a configobj section, in file order. value is the configobj value
with surrounding quotes removed; a configobj list value (comma separated,
unquoted) is joined back with ", " only where a field says so."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ConfigEntry:
    __hash__ = None
    name: str
    value: str

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "value", _cott_validate_abi(self.value, str, path="$.value"))

"""One key of an init-commands section. commands holds the configobj value: a
list value keeps its items in order, a single value is one item, an empty
value is no item."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CommandEntry:
    __hash__ = None
    name: str
    commands: CottList[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "name", _cott_validate_abi(self.name, str, path="$.name"))
        if not _cott_validated_construction():
            object.__setattr__(self, "commands", _cott_validate_abi(self.commands, CottList[str], path="$.commands"))

"""The typed [main] section of the merged configuration, converted exactly as
upstream pgcli reads each key. Booleans use configobj as_bool (case-insensitive
true/false, yes/no, on/off, 1/0); integers use configobj as_int (Python int()).
Strings are the raw values. destructive_warning is configobj as_list (a list
value keeps its items, a single string becomes a one-item list).
max_field_width is Nothing when the key is absent-and-empty, empty, or "none"
(ignoring ASCII case), otherwise Some(max(3, abs(int(value)))); absent means
the default 500. pager is "" when the key is absent (the default file keeps it
commented out). hide_named_query_text and verbose_errors are false when absent.
use_local_timezone is true when absent. prompt defaults to "\\\\u@\\\\h:\\\\d> ",
multi_line_mode to "psql" and null_string to "<null>" when absent.
on_error is the raw value upper-cased."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MainSettings:
    __hash__ = None
    smart_completion: bool
    auto_suggest: bool
    wider_completion_menu: bool
    always_use_single_connection: bool
    multi_line: bool
    multi_line_mode: str
    destructive_warning: CottList[str]
    destructive_warning_restarts_connection: bool
    destructive_statements_require_transaction: bool
    expand: bool
    auto_expand: bool
    auto_retry_closed_connection: bool
    generate_aliases: bool
    alias_map_file: str
    log_file: str
    keyword_casing: str
    casing_file: str
    generate_casing_file: bool
    case_column_headers: bool
    history_file: str
    log_level: str
    asterisk_column_order: str
    qualify_columns: str
    search_path_filter: bool
    pager: str
    timing: bool
    hide_named_query_text: bool
    show_bottom_toolbar: bool
    table_format: str
    syntax_style: str
    vi: bool
    connect_timeout: I64
    on_error: str
    row_limit: I64
    max_field_width: Option[U32]
    less_chatty: bool
    verbose_errors: bool
    prompt: str
    min_num_menu_lines: I64
    multiline_continuation_char: str
    null_string: str
    enable_pager: bool
    keyring: bool
    use_local_timezone: bool

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "smart_completion", _cott_validate_abi(self.smart_completion, bool, path="$.smart_completion"))
        if not _cott_validated_construction():
            object.__setattr__(self, "auto_suggest", _cott_validate_abi(self.auto_suggest, bool, path="$.auto_suggest"))
        if not _cott_validated_construction():
            object.__setattr__(self, "wider_completion_menu", _cott_validate_abi(self.wider_completion_menu, bool, path="$.wider_completion_menu"))
        if not _cott_validated_construction():
            object.__setattr__(self, "always_use_single_connection", _cott_validate_abi(self.always_use_single_connection, bool, path="$.always_use_single_connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "multi_line", _cott_validate_abi(self.multi_line, bool, path="$.multi_line"))
        if not _cott_validated_construction():
            object.__setattr__(self, "multi_line_mode", _cott_validate_abi(self.multi_line_mode, str, path="$.multi_line_mode"))
        if not _cott_validated_construction():
            object.__setattr__(self, "destructive_warning", _cott_validate_abi(self.destructive_warning, CottList[str], path="$.destructive_warning"))
        if not _cott_validated_construction():
            object.__setattr__(self, "destructive_warning_restarts_connection", _cott_validate_abi(self.destructive_warning_restarts_connection, bool, path="$.destructive_warning_restarts_connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "destructive_statements_require_transaction", _cott_validate_abi(self.destructive_statements_require_transaction, bool, path="$.destructive_statements_require_transaction"))
        if not _cott_validated_construction():
            object.__setattr__(self, "expand", _cott_validate_abi(self.expand, bool, path="$.expand"))
        if not _cott_validated_construction():
            object.__setattr__(self, "auto_expand", _cott_validate_abi(self.auto_expand, bool, path="$.auto_expand"))
        if not _cott_validated_construction():
            object.__setattr__(self, "auto_retry_closed_connection", _cott_validate_abi(self.auto_retry_closed_connection, bool, path="$.auto_retry_closed_connection"))
        if not _cott_validated_construction():
            object.__setattr__(self, "generate_aliases", _cott_validate_abi(self.generate_aliases, bool, path="$.generate_aliases"))
        if not _cott_validated_construction():
            object.__setattr__(self, "alias_map_file", _cott_validate_abi(self.alias_map_file, str, path="$.alias_map_file"))
        if not _cott_validated_construction():
            object.__setattr__(self, "log_file", _cott_validate_abi(self.log_file, str, path="$.log_file"))
        if not _cott_validated_construction():
            object.__setattr__(self, "keyword_casing", _cott_validate_abi(self.keyword_casing, str, path="$.keyword_casing"))
        if not _cott_validated_construction():
            object.__setattr__(self, "casing_file", _cott_validate_abi(self.casing_file, str, path="$.casing_file"))
        if not _cott_validated_construction():
            object.__setattr__(self, "generate_casing_file", _cott_validate_abi(self.generate_casing_file, bool, path="$.generate_casing_file"))
        if not _cott_validated_construction():
            object.__setattr__(self, "case_column_headers", _cott_validate_abi(self.case_column_headers, bool, path="$.case_column_headers"))
        if not _cott_validated_construction():
            object.__setattr__(self, "history_file", _cott_validate_abi(self.history_file, str, path="$.history_file"))
        if not _cott_validated_construction():
            object.__setattr__(self, "log_level", _cott_validate_abi(self.log_level, str, path="$.log_level"))
        if not _cott_validated_construction():
            object.__setattr__(self, "asterisk_column_order", _cott_validate_abi(self.asterisk_column_order, str, path="$.asterisk_column_order"))
        if not _cott_validated_construction():
            object.__setattr__(self, "qualify_columns", _cott_validate_abi(self.qualify_columns, str, path="$.qualify_columns"))
        if not _cott_validated_construction():
            object.__setattr__(self, "search_path_filter", _cott_validate_abi(self.search_path_filter, bool, path="$.search_path_filter"))
        if not _cott_validated_construction():
            object.__setattr__(self, "pager", _cott_validate_abi(self.pager, str, path="$.pager"))
        if not _cott_validated_construction():
            object.__setattr__(self, "timing", _cott_validate_abi(self.timing, bool, path="$.timing"))
        if not _cott_validated_construction():
            object.__setattr__(self, "hide_named_query_text", _cott_validate_abi(self.hide_named_query_text, bool, path="$.hide_named_query_text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "show_bottom_toolbar", _cott_validate_abi(self.show_bottom_toolbar, bool, path="$.show_bottom_toolbar"))
        if not _cott_validated_construction():
            object.__setattr__(self, "table_format", _cott_validate_abi(self.table_format, str, path="$.table_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "syntax_style", _cott_validate_abi(self.syntax_style, str, path="$.syntax_style"))
        if not _cott_validated_construction():
            object.__setattr__(self, "vi", _cott_validate_abi(self.vi, bool, path="$.vi"))
        if not _cott_validated_construction():
            object.__setattr__(self, "connect_timeout", _cott_validate_abi(self.connect_timeout, I64, path="$.connect_timeout"))
        if not _cott_validated_construction():
            object.__setattr__(self, "on_error", _cott_validate_abi(self.on_error, str, path="$.on_error"))
        if not _cott_validated_construction():
            object.__setattr__(self, "row_limit", _cott_validate_abi(self.row_limit, I64, path="$.row_limit"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_field_width", _cott_validate_abi(self.max_field_width, Option[U32], path="$.max_field_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "less_chatty", _cott_validate_abi(self.less_chatty, bool, path="$.less_chatty"))
        if not _cott_validated_construction():
            object.__setattr__(self, "verbose_errors", _cott_validate_abi(self.verbose_errors, bool, path="$.verbose_errors"))
        if not _cott_validated_construction():
            object.__setattr__(self, "prompt", _cott_validate_abi(self.prompt, str, path="$.prompt"))
        if not _cott_validated_construction():
            object.__setattr__(self, "min_num_menu_lines", _cott_validate_abi(self.min_num_menu_lines, I64, path="$.min_num_menu_lines"))
        if not _cott_validated_construction():
            object.__setattr__(self, "multiline_continuation_char", _cott_validate_abi(self.multiline_continuation_char, str, path="$.multiline_continuation_char"))
        if not _cott_validated_construction():
            object.__setattr__(self, "null_string", _cott_validate_abi(self.null_string, str, path="$.null_string"))
        if not _cott_validated_construction():
            object.__setattr__(self, "enable_pager", _cott_validate_abi(self.enable_pager, bool, path="$.enable_pager"))
        if not _cott_validated_construction():
            object.__setattr__(self, "keyring", _cott_validate_abi(self.keyring, bool, path="$.keyring"))
        if not _cott_validated_construction():
            object.__setattr__(self, "use_local_timezone", _cott_validate_abi(self.use_local_timezone, bool, path="$.use_local_timezone"))

"""The merged pgcli configuration: the built-in PGCLI_DEFAULT_CONFIG merged with
the user's file (user keys override default keys, sections merge key by key,
extra user keys and sections are kept). Section lists keep merged configobj key
order (default keys first in default order, then keys only the user file has).
colors is [colors]; named_queries is [named queries]; alias_dsn is [alias_dsn];
init_commands is [init-commands]; alias_dsn_init_commands is
[alias_dsn.init-commands]; decimal_format and float_format are [data_formats]
decimal and float; column_date_formats is [column_date_formats]; ssh_tunnels is
[ssh tunnels] and dsn_ssh_tunnels is [dsn ssh tunnels]. A missing optional
section is an empty list. A list value in a ConfigEntry section is joined with
", "."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PgcliConfig:
    __hash__ = None
    main: MainSettings
    colors: CottList[ConfigEntry]
    named_queries: CottList[ConfigEntry]
    alias_dsn: CottList[ConfigEntry]
    init_commands: CottList[CommandEntry]
    alias_dsn_init_commands: CottList[CommandEntry]
    decimal_format: str
    float_format: str
    column_date_formats: CottList[ConfigEntry]
    ssh_tunnels: CottList[ConfigEntry]
    dsn_ssh_tunnels: CottList[ConfigEntry]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "main", _cott_validate_abi(self.main, MainSettings, path="$.main"))
        if not _cott_validated_construction():
            object.__setattr__(self, "colors", _cott_validate_abi(self.colors, CottList[ConfigEntry], path="$.colors"))
        if not _cott_validated_construction():
            object.__setattr__(self, "named_queries", _cott_validate_abi(self.named_queries, CottList[ConfigEntry], path="$.named_queries"))
        if not _cott_validated_construction():
            object.__setattr__(self, "alias_dsn", _cott_validate_abi(self.alias_dsn, CottList[ConfigEntry], path="$.alias_dsn"))
        if not _cott_validated_construction():
            object.__setattr__(self, "init_commands", _cott_validate_abi(self.init_commands, CottList[CommandEntry], path="$.init_commands"))
        if not _cott_validated_construction():
            object.__setattr__(self, "alias_dsn_init_commands", _cott_validate_abi(self.alias_dsn_init_commands, CottList[CommandEntry], path="$.alias_dsn_init_commands"))
        if not _cott_validated_construction():
            object.__setattr__(self, "decimal_format", _cott_validate_abi(self.decimal_format, str, path="$.decimal_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "float_format", _cott_validate_abi(self.float_format, str, path="$.float_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "column_date_formats", _cott_validate_abi(self.column_date_formats, CottList[ConfigEntry], path="$.column_date_formats"))
        if not _cott_validated_construction():
            object.__setattr__(self, "ssh_tunnels", _cott_validate_abi(self.ssh_tunnels, CottList[ConfigEntry], path="$.ssh_tunnels"))
        if not _cott_validated_construction():
            object.__setattr__(self, "dsn_ssh_tunnels", _cott_validate_abi(self.dsn_ssh_tunnels, CottList[ConfigEntry], path="$.dsn_ssh_tunnels"))

"""config_location() on a POSIX host. With xdg_config_home Some(value) (the
XDG_CONFIG_HOME variable is set, even to ""), return value with a leading
"~" expanded to home (os.path.expanduser semantics with HOME = home)
followed by "/pgcli/". Otherwise return home + "/.config/pgcli/". The result
always ends with "/"; files inside are named by appending "config",
"history", "log" or "casing"."""
"""load_config(user, default) without file access: parse PGCLI_DEFAULT_CONFIG
and user_text with the lock-selected configobj (ConfigObj(text.splitlines(),
interpolation=False) for each, then cfg = ConfigObj(), cfg.merge(default),
cfg.merge(user)) and convert the merged tree into PgcliConfig as the field
docs describe. A configobj ParseError (including DuplicateError) or a failed
as_bool/as_int/int() conversion is Invalid(message: str(error)).
Conversions happen in MainSettings field order, and the first failure is
returned."""
"""get_config(pgclirc_file) on the host file system: path is the pgclirc
location (it may start with "~", expanded with os.path.expanduser). When the expanded path does not
exist, create its parent directories (os.makedirs, exist_ok) and write
PGCLI_DEFAULT_CONFIG to it byte for byte (UTF-8). Then read the file as
UTF-8 and return parse_pgcli_config(its text). An OSError while creating,
writing or reading is Unreadable(path: the expanded path, message: str(error))."""
"""initialize_logging: the log path is config_directory + "log" when log_file
is "default", otherwise log_file with "~" expanded. Create its parent
directories (exist_ok). log_level (compared upper-cased) must be one of
CRITICAL, ERROR, WARNING, INFO, DEBUG, NONE, else Invalid(message:
"Unknown log level: " + log_level). NONE installs a logging.NullHandler and
level CRITICAL; any other level installs a logging.FileHandler on the log
path (append mode, UTF-8) with the formatter "%(asctime)s (%(process)d/%(threadName)s)
__omp_magic("", "(name)s %(levelname)s - %(message)s\\" and that level. The same handler and")
level are attached to both the "pgcli" and the "pgspecial" loggers. Then log
at DEBUG on "pgcli" the messages "Initializing pgcli logging." and
"Log file %r." with the log path. Returns the log path. An OSError is
Unreadable(path: the log path, message: str(error))."""
__all__ = ["CommandEntry", "ConfigEntry", "ConfigError", "ConfigError_Invalid", "ConfigError_Unreadable", "MainSettings", "PGCLI_DEFAULT_CONFIG", "PgcliConfig"]
