from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.pgcli.config_types import CommandEntry as CommandEntry, ConfigEntry as ConfigEntry, ConfigError as ConfigError, ConfigError_Invalid as ConfigError_Invalid, ConfigError_Unreadable as ConfigError_Unreadable, MainSettings as MainSettings, PGCLI_DEFAULT_CONFIG as PGCLI_DEFAULT_CONFIG, PgcliConfig as PgcliConfig
"""config_location() on a POSIX host. With xdg_config_home Some(value) (the
XDG_CONFIG_HOME variable is set, even to ""), return value with a leading
"~" expanded to home (os.path.expanduser semantics with HOME = home)
followed by "/pgcli/". Otherwise return home + "/.config/pgcli/". The result
always ends with "/"; files inside are named by appending "config",
"history", "log" or "casing"."""
def pgcli_config_directory(xdg_config_home: Option[str], home: str) -> str: ...

"""load_config(user, default) without file access: parse PGCLI_DEFAULT_CONFIG
and user_text with the lock-selected configobj (ConfigObj(text.splitlines(),
interpolation=False) for each, then cfg = ConfigObj(), cfg.merge(default),
cfg.merge(user)) and convert the merged tree into PgcliConfig as the field
docs describe. A configobj ParseError (including DuplicateError) or a failed
as_bool/as_int/int() conversion is Invalid(message: str(error)).
Conversions happen in MainSettings field order, and the first failure is
returned."""
def parse_pgcli_config(user_text: str) -> Result[PgcliConfig, ConfigError]: ...

"""get_config(pgclirc_file) on the host file system: path is the pgclirc
location (it may start with "~", expanded with os.path.expanduser). When the expanded path does not
exist, create its parent directories (os.makedirs, exist_ok) and write
PGCLI_DEFAULT_CONFIG to it byte for byte (UTF-8). Then read the file as
UTF-8 and return parse_pgcli_config(its text). An OSError while creating,
writing or reading is Unreadable(path: the expanded path, message: str(error))."""
def load_pgcli_config(path: Path) -> Result[PgcliConfig, ConfigError]: ...

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
def configure_pgcli_logging(log_file: str, log_level: str, config_directory: str) -> Result[str, ConfigError]: ...

__all__ = ["CommandEntry", "ConfigEntry", "ConfigError", "ConfigError_Invalid", "ConfigError_Unreadable", "MainSettings", "PGCLI_DEFAULT_CONFIG", "PgcliConfig", "configure_pgcli_logging", "load_pgcli_config", "parse_pgcli_config", "pgcli_config_directory"]
