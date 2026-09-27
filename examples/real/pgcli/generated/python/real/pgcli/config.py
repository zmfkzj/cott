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

from real.pgcli.config_types import CommandEntry, ConfigEntry, ConfigError, ConfigError_Invalid, ConfigError_Unreadable, MainSettings, PGCLI_DEFAULT_CONFIG, PgcliConfig

def pgcli_config_directory(xdg_config_home: Option[str], home: str) -> str:
    """config_location() on a POSIX host. With xdg_config_home Some(value) (the
XDG_CONFIG_HOME variable is set, even to ""), return value with a leading
"~" expanded to home (os.path.expanduser semantics with HOME = home)
followed by "/pgcli/". Otherwise return home + "/.config/pgcli/". The result
always ends with "/"; files inside are named by appending "config",
"history", "log" or "casing"."""
    xdg_config_home = _cott_validate_abi(xdg_config_home, Option[str], path="$.xdg_config_home")
    home = _cott_validate_abi(home, str, path="$.home")
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/config/pgcli_config_directory.py", "adad3353c244aa044c1fcbc23e7c2007b70a12a7b3f87f5b83886f6d3510ef00", "pgcli_config_directory", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.config.pgcli_config_directory")
        _result = _implementation(xdg_config_home, home)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.config.pgcli_config_directory"
        if _error.span is None:
            _error.span = {"end_byte":16044,"end_column":1,"end_line":135,"start_byte":15473,"start_column":1,"start_line":121}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.config.pgcli_config_directory", phase="implementation-call", span={"end_byte":16044,"end_column":1,"end_line":135,"start_byte":15473,"start_column":1,"start_line":121}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.config.pgcli_config_directory", phase="implementation-call", span={"end_byte":16044,"end_column":1,"end_line":135,"start_byte":15473,"start_column":1,"start_line":121}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, str, path="$.return")
    if not (_cott_contract_condition((_cott_ends_with(_result, "/pgcli/")), "real.pgcli.config.pgcli_config_directory", "ensures:1")):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.config.pgcli_config_directory", clause="ensures:1", phase="ensures", span={"end_byte":16026,"end_column":43,"end_line":131,"start_byte":15988,"start_column":5,"start_line":131}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=_cott_validate_abi)
    return _result

def parse_pgcli_config(user_text: str) -> Result[PgcliConfig, ConfigError]:
    """load_config(user, default) without file access: parse PGCLI_DEFAULT_CONFIG
and user_text with the lock-selected configobj (ConfigObj(text.splitlines(),
interpolation=False) for each, then cfg = ConfigObj(), cfg.merge(default),
cfg.merge(user)) and convert the merged tree into PgcliConfig as the field
docs describe. A configobj ParseError (including DuplicateError) or a failed
as_bool/as_int/int() conversion is Invalid(message: str(error)).
Conversions happen in MainSettings field order, and the first failure is
returned."""
    user_text = _cott_validate_abi(user_text, str, path="$.user_text")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/config/parse_pgcli_config.py", "471a9b1593ab7daa225c44af1316203ea05680d441dcca2de5bdb6cac4ad36d5", "parse_pgcli_config", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.config.parse_pgcli_config")
        _result = _implementation(user_text)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.config.parse_pgcli_config"
        if _error.span is None:
            _error.span = {"end_byte":16874,"end_column":1,"end_line":153,"start_byte":16044,"start_column":1,"start_line":135}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.config.parse_pgcli_config", phase="implementation-call", span={"end_byte":16874,"end_column":1,"end_line":153,"start_byte":16044,"start_column":1,"start_line":135}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.config.parse_pgcli_config", phase="implementation-call", span={"end_byte":16874,"end_column":1,"end_line":153,"start_byte":16044,"start_column":1,"start_line":135}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[PgcliConfig, ConfigError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.config.parse_pgcli_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConfigError_Invalid,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.config.parse_pgcli_config", phase="error", span={"end_byte":16874,"end_column":1,"end_line":153,"start_byte":16044,"start_column":1,"start_line":135}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.config.parse_pgcli_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.config.parse_pgcli_config", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConfigError_Invalid:
        _cott_contract_condition(True, "real.pgcli.config.parse_pgcli_config", "error:2")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            config = _cott_match_value.value
            return (_cott_contract_condition((((not ("stop" in ((config).main).on_error)) and (not ("resume" in ((config).main).on_error)))), "real.pgcli.config.parse_pgcli_config", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.config.parse_pgcli_config", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.config.parse_pgcli_config", clause="ensures:1", phase="ensures", span={"end_byte":16825,"end_column":127,"end_line":147,"start_byte":16703,"start_column":5,"start_line":147}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[PgcliConfig, ConfigError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_pgcli_config(path: Path) -> Result[PgcliConfig, ConfigError]:
    """get_config(pgclirc_file) on the host file system: path is the pgclirc
location (it may start with "~", expanded with os.path.expanduser). When the expanded path does not
exist, create its parent directories (os.makedirs, exist_ok) and write
PGCLI_DEFAULT_CONFIG to it byte for byte (UTF-8). Then read the file as
UTF-8 and return parse_pgcli_config(its text). An OSError while creating,
writing or reading is Unreadable(path: the expanded path, message: str(error))."""
    path = _cott_validate_abi(path, Path, path="$.path")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/config/load_pgcli_config.py", "94d3e177763f72abe510145ef2fc144465a281343da301a1fff065f32fca59aa", "load_pgcli_config", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.config.load_pgcli_config")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.config.load_pgcli_config"
        if _error.span is None:
            _error.span = {"end_byte":17685,"end_column":1,"end_line":170,"start_byte":16874,"start_column":1,"start_line":153}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.config.load_pgcli_config", phase="implementation-call", span={"end_byte":17685,"end_column":1,"end_line":170,"start_byte":16874,"start_column":1,"start_line":153}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.config.load_pgcli_config", phase="implementation-call", span={"end_byte":17685,"end_column":1,"end_line":170,"start_byte":16874,"start_column":1,"start_line":153}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[PgcliConfig, ConfigError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.config.load_pgcli_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConfigError_Unreadable, ConfigError_Invalid,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.config.load_pgcli_config", phase="error", span={"end_byte":17685,"end_column":1,"end_line":170,"start_byte":16874,"start_column":1,"start_line":153}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.config.load_pgcli_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.config.load_pgcli_config", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConfigError_Unreadable:
        _cott_contract_condition(True, "real.pgcli.config.load_pgcli_config", "error:2")
    if type(_result) is Err and type(_result.error) is ConfigError_Invalid:
        _cott_contract_condition(True, "real.pgcli.config.load_pgcli_config", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            config = _cott_match_value.value
            return (_cott_contract_condition((((not ("stop" in ((config).main).on_error)) and (not ("resume" in ((config).main).on_error)))), "real.pgcli.config.load_pgcli_config", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.config.load_pgcli_config", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.config.load_pgcli_config", clause="ensures:1", phase="ensures", span={"end_byte":17582,"end_column":127,"end_line":163,"start_byte":17460,"start_column":5,"start_line":163}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[PgcliConfig, ConfigError], path="$.return", validator=_cott_validate_abi)
    return _result

def configure_pgcli_logging(log_file: str, log_level: str, config_directory: str) -> Result[str, ConfigError]:
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
    log_file = _cott_validate_abi(log_file, str, path="$.log_file")
    log_level = _cott_validate_abi(log_level, str, path="$.log_level")
    config_directory = _cott_validate_abi(config_directory, str, path="$.config_directory")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/pgcli/config/configure_pgcli_logging.py", "e862f3da4b0949b84ea50f154ef022f7327d9e25b580101bd6f6511a2c1215a6", "configure_pgcli_logging", expected_project_name="real-pgcli", expected_cott_symbol="real.pgcli.config.configure_pgcli_logging")
        _result = _implementation(log_file, log_level, config_directory)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.pgcli.config.configure_pgcli_logging"
        if _error.span is None:
            _error.span = {"end_byte":18998,"end_column":1,"end_line":197,"start_byte":17685,"start_column":1,"start_line":170}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.pgcli.config.configure_pgcli_logging", phase="implementation-call", span={"end_byte":18998,"end_column":1,"end_line":197,"start_byte":17685,"start_column":1,"start_line":170}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.pgcli.config.configure_pgcli_logging", phase="implementation-call", span={"end_byte":18998,"end_column":1,"end_line":197,"start_byte":17685,"start_column":1,"start_line":170}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[str, ConfigError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="real.pgcli.config.configure_pgcli_logging", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (ConfigError_Invalid, ConfigError_Unreadable,):
            raise CottContractViolation("returned error is not allowed", symbol="real.pgcli.config.configure_pgcli_logging", phase="error", span={"end_byte":18998,"end_column":1,"end_line":197,"start_byte":17685,"start_column":1,"start_line":170}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="real.pgcli.config.configure_pgcli_logging", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "real.pgcli.config.configure_pgcli_logging", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is ConfigError_Invalid:
        _cott_contract_condition(True, "real.pgcli.config.configure_pgcli_logging", "error:2")
    if type(_result) is Err and type(_result.error) is ConfigError_Unreadable:
        _cott_contract_condition(True, "real.pgcli.config.configure_pgcli_logging", "error:3")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            log_path = _cott_match_value.value
            return (_cott_contract_condition((((log_file != "default") or (_cott_starts_with(log_path, config_directory) and _cott_ends_with(log_path, "log")))), "real.pgcli.config.configure_pgcli_logging", "ensures:1"))
        _cott_contract_condition((False), "real.pgcli.config.configure_pgcli_logging", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="real.pgcli.config.configure_pgcli_logging", clause="ensures:1", phase="ensures", span={"end_byte":18895,"end_column":135,"end_line":190,"start_byte":18765,"start_column":5,"start_line":190}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[str, ConfigError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["CommandEntry", "ConfigEntry", "ConfigError", "ConfigError_Invalid", "ConfigError_Unreadable", "MainSettings", "PGCLI_DEFAULT_CONFIG", "PgcliConfig", "configure_pgcli_logging", "load_pgcli_config", "parse_pgcli_config", "pgcli_config_directory"]
