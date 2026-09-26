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

from frogmouth.storage_types import LoadedBookmarks, LoadedConfig, StoreError, StoreError_Malformed, StoreError_ReadFailed, StoreError_WriteFailed, StoredFile
from frogmouth.bookmarks_types import Bookmark
from frogmouth.config_types import Config
from frogmouth.history_types import History
from frogmouth.model_types import Dialog, Location

def load_config(config_directory: str) -> Result[LoadedConfig, StoreError]:
    """Load the configuration file named configuration.json in config_directory
(joined with one "/"). The file is strict UTF-8 JSON holding an object;
its "light_mode" boolean selects Light (true) or Dark (false), its
"markdown_extensions" array of strings becomes markdown_extensions in
order, and its "navigation_left" boolean selects Left (true) or Right
(false). A missing key takes the value of
frogmouth.config.default_config(); other keys are ignored. When the file
does not exist, frogmouth.storage.save_config(config_directory,
default_config()) stores the defaults and they are returned. path is the
configuration file path.

Every StoreError carries the configuration file path. Bytes that are not
UTF-8 JSON, a non-object document or a value of the wrong JSON type is
Malformed; any other read failure is ReadFailed; a failed default save is
returned unchanged.

Files are read from the file system the program runs against: the fs
fixture root while a Cott scenario with an fs fixture is active,
otherwise the host file system."""
    config_directory = _cott_validate_abi(config_directory, str, path="$.config_directory")
    if not (_cott_contract_condition(((len(config_directory) > 0)), "frogmouth.storage.load_config", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.storage.load_config", clause="requires:1", phase="requires", span={"end_byte":2263,"end_column":38,"end_line":66,"start_byte":2230,"start_column":5,"start_line":66}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/storage/load_config.py", "0c2e53b6ce556171afb0135a3aa5565a5eda94db32a2779765742d21783f5010", "load_config", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.storage.load_config")
        _result = _implementation(config_directory)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.storage.load_config"
        if _error.span is None:
            _error.span = {"end_byte":2753,"end_column":1,"end_line":78,"start_byte":1019,"start_column":1,"start_line":43}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.storage.load_config", phase="implementation-call", span={"end_byte":2753,"end_column":1,"end_line":78,"start_byte":1019,"start_column":1,"start_line":43}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.storage.load_config", phase="implementation-call", span={"end_byte":2753,"end_column":1,"end_line":78,"start_byte":1019,"start_column":1,"start_line":43}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[LoadedConfig, StoreError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.storage.load_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StoreError_Malformed, StoreError_ReadFailed, StoreError_WriteFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.storage.load_config", phase="error", span={"end_byte":2753,"end_column":1,"end_line":78,"start_byte":1019,"start_column":1,"start_line":43}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.storage.load_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "frogmouth.storage.load_config", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is StoreError_Malformed:
        _cott_contract_condition(True, "frogmouth.storage.load_config", "error:5")
    if type(_result) is Err and type(_result.error) is StoreError_ReadFailed:
        _cott_contract_condition(True, "frogmouth.storage.load_config", "error:6")
    if type(_result) is Err and type(_result.error) is StoreError_WriteFailed:
        _cott_contract_condition(True, "frogmouth.storage.load_config", "error:7")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            loaded = _cott_match_value.value
            return (_cott_contract_condition((_cott_starts_with((loaded).path, config_directory)), "frogmouth.storage.load_config", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.storage.load_config", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.load_config", clause="ensures:2", phase="ensures", span={"end_byte":2340,"end_column":76,"end_line":68,"start_byte":2269,"start_column":5,"start_line":68}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is StoreError_Malformed and True and True:
            path = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((_cott_starts_with(path, config_directory) and _cott_ends_with(path, "/configuration.json"))), "frogmouth.storage.load_config", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.storage.load_config", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.load_config", clause="ensures:3", phase="ensures", span={"end_byte":2478,"end_column":138,"end_line":69,"start_byte":2345,"start_column":5,"start_line":69}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is StoreError_ReadFailed and True and True:
            path = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((_cott_starts_with(path, config_directory) and _cott_ends_with(path, "/configuration.json"))), "frogmouth.storage.load_config", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.storage.load_config", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.load_config", clause="ensures:4", phase="ensures", span={"end_byte":2617,"end_column":139,"end_line":70,"start_byte":2483,"start_column":5,"start_line":70}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[LoadedConfig, StoreError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_config(config_directory: str, config: Config) -> Result[StoredFile, StoreError]:
    """Store config as configuration.json in config_directory, creating missing
directories. The content is the JSON object with the keys "light_mode"
(true for Light), "markdown_extensions" and "navigation_left" (true for
Left) in that order, serialized like Python json.dumps with indent=4 and
the default ASCII escaping, without a trailing newline. The file is
replaced atomically, so a failed save leaves the previous file intact,
and every failure is WriteFailed carrying the file path."""
    config_directory = _cott_validate_abi(config_directory, str, path="$.config_directory")
    config = _cott_validate_abi(config, Config, path="$.config")
    if not (_cott_contract_condition(((len(config_directory) > 0)), "frogmouth.storage.save_config", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.storage.save_config", clause="requires:1", phase="requires", span={"end_byte":3413,"end_column":38,"end_line":89,"start_byte":3380,"start_column":5,"start_line":89}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/storage/save_config.py", "d01a9425c2da05448a8de9a7c6d018d060bb93d4953f2bf72c5ad782e1b389c4", "save_config", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.storage.save_config")
        _result = _implementation(config_directory, config)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.storage.save_config"
        if _error.span is None:
            _error.span = {"end_byte":3702,"end_column":1,"end_line":98,"start_byte":2753,"start_column":1,"start_line":78}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.storage.save_config", phase="implementation-call", span={"end_byte":3702,"end_column":1,"end_line":98,"start_byte":2753,"start_column":1,"start_line":78}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.storage.save_config", phase="implementation-call", span={"end_byte":3702,"end_column":1,"end_line":98,"start_byte":2753,"start_column":1,"start_line":78}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[StoredFile, StoreError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.storage.save_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StoreError_WriteFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.storage.save_config", phase="error", span={"end_byte":3702,"end_column":1,"end_line":98,"start_byte":2753,"start_column":1,"start_line":78}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.storage.save_config", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "frogmouth.storage.save_config", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is StoreError_WriteFailed:
        _cott_contract_condition(True, "frogmouth.storage.save_config", "error:4")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            stored = _cott_match_value.value
            return (_cott_contract_condition(((_cott_starts_with((stored).path, config_directory) and _cott_ends_with((stored).path, "/configuration.json"))), "frogmouth.storage.save_config", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.storage.save_config", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.save_config", clause="ensures:2", phase="ensures", span={"end_byte":3542,"end_column":128,"end_line":91,"start_byte":3419,"start_column":5,"start_line":91}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is StoreError_WriteFailed and True and True:
            path = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition((_cott_ends_with(path, "/configuration.json")), "frogmouth.storage.save_config", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.storage.save_config", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.save_config", clause="ensures:3", phase="ensures", span={"end_byte":3640,"end_column":98,"end_line":92,"start_byte":3547,"start_column":5,"start_line":92}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[StoredFile, StoreError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_history(data_directory: str) -> Result[History, StoreError]:
    """Load the saved history from history.json in data_directory (joined with
one "/") and return frogmouth.history.start_history of its locations. An
absent file is an empty history. The file is strict UTF-8 JSON holding
an array of non-empty strings, oldest first; a string for which
frogmouth.locations.remote_location returns a location becomes that
Remote location, any other string a Local location with that target.

Every StoreError carries the history file path. Bytes that are not UTF-8
JSON, a non-array document, or an element that is not a non-empty string
is Malformed; any other read failure is ReadFailed.

Files are read from the file system the program runs against: the fs
fixture root while a Cott scenario with an fs fixture is active,
otherwise the host file system."""
    data_directory = _cott_validate_abi(data_directory, str, path="$.data_directory")
    if not (_cott_contract_condition(((len(data_directory) > 0)), "frogmouth.storage.load_history", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.storage.load_history", clause="requires:1", phase="requires", span={"end_byte":4666,"end_column":36,"end_line":116,"start_byte":4635,"start_column":5,"start_line":116}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/storage/load_history.py", "365ea4f77b3d47fc7f7c27ba1f7aa8f04f89d24dcf559106520f31a1bae97a60", "load_history", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.storage.load_history")
        _result = _implementation(data_directory)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.storage.load_history"
        if _error.span is None:
            _error.span = {"end_byte":5127,"end_column":1,"end_line":127,"start_byte":3702,"start_column":1,"start_line":98}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.storage.load_history", phase="implementation-call", span={"end_byte":5127,"end_column":1,"end_line":127,"start_byte":3702,"start_column":1,"start_line":98}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.storage.load_history", phase="implementation-call", span={"end_byte":5127,"end_column":1,"end_line":127,"start_byte":3702,"start_column":1,"start_line":98}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[History, StoreError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.storage.load_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StoreError_Malformed, StoreError_ReadFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.storage.load_history", phase="error", span={"end_byte":5127,"end_column":1,"end_line":127,"start_byte":3702,"start_column":1,"start_line":98}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.storage.load_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "frogmouth.storage.load_history", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is StoreError_Malformed:
        _cott_contract_condition(True, "frogmouth.storage.load_history", "error:5")
    if type(_result) is Err and type(_result.error) is StoreError_ReadFailed:
        _cott_contract_condition(True, "frogmouth.storage.load_history", "error:6")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            loaded = _cott_match_value.value
            return (_cott_contract_condition((((not (len((loaded).locations) > 0)) or (((loaded).current + 1) == len((loaded).locations)))), "frogmouth.storage.load_history", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.storage.load_history", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.load_history", clause="ensures:2", phase="ensures", span={"end_byte":4775,"end_column":108,"end_line":118,"start_byte":4672,"start_column":5,"start_line":118}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is StoreError_Malformed and True and True:
            path = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((_cott_starts_with(path, data_directory) and _cott_ends_with(path, "/history.json"))), "frogmouth.storage.load_history", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.storage.load_history", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.load_history", clause="ensures:3", phase="ensures", span={"end_byte":4905,"end_column":130,"end_line":119,"start_byte":4780,"start_column":5,"start_line":119}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is StoreError_ReadFailed and True and True:
            path = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((_cott_starts_with(path, data_directory) and _cott_ends_with(path, "/history.json"))), "frogmouth.storage.load_history", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.storage.load_history", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.load_history", clause="ensures:4", phase="ensures", span={"end_byte":5036,"end_column":131,"end_line":120,"start_byte":4910,"start_column":5,"start_line":120}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[History, StoreError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_history(data_directory: str, locations: CottList[Location]) -> Result[StoredFile, StoreError]:
    """Store locations as history.json in data_directory, creating missing
directories: a JSON array of the location targets in order, serialized
like Python json.dumps with indent=4 and the default ASCII escaping,
without a trailing newline. The file is replaced atomically, so a failed
save leaves the previous file intact, and every failure is WriteFailed
carrying the file path."""
    data_directory = _cott_validate_abi(data_directory, str, path="$.data_directory")
    locations = _cott_validate_abi(locations, CottList[Location], path="$.locations")
    if not (_cott_contract_condition(((len(data_directory) > 0)), "frogmouth.storage.save_history", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.storage.save_history", clause="requires:1", phase="requires", span={"end_byte":5682,"end_column":36,"end_line":137,"start_byte":5651,"start_column":5,"start_line":137}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/storage/save_history.py", "b7f0fda1bb9af969daeab9b667ae9c40d3b5c3f35b3acf76f5ae0ffeae901958", "save_history", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.storage.save_history")
        _result = _implementation(data_directory, locations)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.storage.save_history"
        if _error.span is None:
            _error.span = {"end_byte":5957,"end_column":1,"end_line":146,"start_byte":5127,"start_column":1,"start_line":127}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.storage.save_history", phase="implementation-call", span={"end_byte":5957,"end_column":1,"end_line":146,"start_byte":5127,"start_column":1,"start_line":127}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.storage.save_history", phase="implementation-call", span={"end_byte":5957,"end_column":1,"end_line":146,"start_byte":5127,"start_column":1,"start_line":127}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[StoredFile, StoreError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.storage.save_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StoreError_WriteFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.storage.save_history", phase="error", span={"end_byte":5957,"end_column":1,"end_line":146,"start_byte":5127,"start_column":1,"start_line":127}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.storage.save_history", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "frogmouth.storage.save_history", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is StoreError_WriteFailed:
        _cott_contract_condition(True, "frogmouth.storage.save_history", "error:4")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            stored = _cott_match_value.value
            return (_cott_contract_condition(((_cott_starts_with((stored).path, data_directory) and _cott_ends_with((stored).path, "/history.json"))), "frogmouth.storage.save_history", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.storage.save_history", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.save_history", clause="ensures:2", phase="ensures", span={"end_byte":5803,"end_column":120,"end_line":139,"start_byte":5688,"start_column":5,"start_line":139}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is StoreError_WriteFailed and True and True:
            path = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition((_cott_ends_with(path, "/history.json")), "frogmouth.storage.save_history", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.storage.save_history", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.save_history", clause="ensures:3", phase="ensures", span={"end_byte":5895,"end_column":92,"end_line":140,"start_byte":5808,"start_column":5,"start_line":140}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[StoredFile, StoreError], path="$.return", validator=_cott_validate_abi)
    return _result

def load_bookmarks(data_directory: str) -> Result[LoadedBookmarks, StoreError]:
    """Load bookmarks.json from data_directory (joined with one "/"); an absent
file holds no bookmarks. The file is strict UTF-8 JSON holding an array
of two-element arrays [title, location] of non-empty strings, kept in
file order. A location for which frogmouth.locations.remote_location
returns a location becomes that Remote location, any other a Local
location with that target. path is the bookmarks file path.

Every StoreError carries the bookmarks file path. Bytes that are not
UTF-8 JSON, a non-array document or an element of another shape is
Malformed; any other read failure is ReadFailed.

Files are read from the file system the program runs against: the fs
fixture root while a Cott scenario with an fs fixture is active,
otherwise the host file system."""
    data_directory = _cott_validate_abi(data_directory, str, path="$.data_directory")
    if not (_cott_contract_condition(((len(data_directory) > 0)), "frogmouth.storage.load_bookmarks", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.storage.load_bookmarks", clause="requires:1", phase="requires", span={"end_byte":6912,"end_column":36,"end_line":164,"start_byte":6881,"start_column":5,"start_line":164}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/storage/load_bookmarks.py", "81fefc312690cb64da0eb5b28ece5280bf2a5bb590b260d132b1ac4a21d4cb99", "load_bookmarks", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.storage.load_bookmarks")
        _result = _implementation(data_directory)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.storage.load_bookmarks"
        if _error.span is None:
            _error.span = {"end_byte":7343,"end_column":1,"end_line":175,"start_byte":5957,"start_column":1,"start_line":146}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.storage.load_bookmarks", phase="implementation-call", span={"end_byte":7343,"end_column":1,"end_line":175,"start_byte":5957,"start_column":1,"start_line":146}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.storage.load_bookmarks", phase="implementation-call", span={"end_byte":7343,"end_column":1,"end_line":175,"start_byte":5957,"start_column":1,"start_line":146}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[LoadedBookmarks, StoreError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.storage.load_bookmarks", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StoreError_Malformed, StoreError_ReadFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.storage.load_bookmarks", phase="error", span={"end_byte":7343,"end_column":1,"end_line":175,"start_byte":5957,"start_column":1,"start_line":146}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.storage.load_bookmarks", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "frogmouth.storage.load_bookmarks", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is StoreError_Malformed:
        _cott_contract_condition(True, "frogmouth.storage.load_bookmarks", "error:5")
    if type(_result) is Err and type(_result.error) is StoreError_ReadFailed:
        _cott_contract_condition(True, "frogmouth.storage.load_bookmarks", "error:6")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            loaded = _cott_match_value.value
            return (_cott_contract_condition((_cott_starts_with((loaded).path, data_directory)), "frogmouth.storage.load_bookmarks", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.storage.load_bookmarks", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.load_bookmarks", clause="ensures:2", phase="ensures", span={"end_byte":6987,"end_column":74,"end_line":166,"start_byte":6918,"start_column":5,"start_line":166}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is StoreError_Malformed and True and True:
            path = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((_cott_starts_with(path, data_directory) and _cott_ends_with(path, "/bookmarks.json"))), "frogmouth.storage.load_bookmarks", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.storage.load_bookmarks", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.load_bookmarks", clause="ensures:3", phase="ensures", span={"end_byte":7119,"end_column":132,"end_line":167,"start_byte":6992,"start_column":5,"start_line":167}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is StoreError_ReadFailed and True and True:
            path = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition(((_cott_starts_with(path, data_directory) and _cott_ends_with(path, "/bookmarks.json"))), "frogmouth.storage.load_bookmarks", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.storage.load_bookmarks", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.load_bookmarks", clause="ensures:4", phase="ensures", span={"end_byte":7252,"end_column":133,"end_line":168,"start_byte":7124,"start_column":5,"start_line":168}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[LoadedBookmarks, StoreError], path="$.return", validator=_cott_validate_abi)
    return _result

def save_bookmarks(data_directory: str, bookmarks: CottList[Bookmark]) -> Result[StoredFile, StoreError]:
    """Store bookmarks as bookmarks.json in data_directory, creating missing
directories: a JSON array holding [title, target] for each bookmark in
order, serialized like Python json.dumps with indent=4 and the default
ASCII escaping, without a trailing newline. The file is replaced
atomically, so a failed save leaves the previous file intact, and every
failure is WriteFailed carrying the file path."""
    data_directory = _cott_validate_abi(data_directory, str, path="$.data_directory")
    bookmarks = _cott_validate_abi(bookmarks, CottList[Bookmark], path="$.bookmarks")
    if not (_cott_contract_condition(((len(data_directory) > 0)), "frogmouth.storage.save_bookmarks", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.storage.save_bookmarks", clause="requires:1", phase="requires", span={"end_byte":7920,"end_column":36,"end_line":185,"start_byte":7889,"start_column":5,"start_line":185}, expected="true", actual="false")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/storage/save_bookmarks.py", "346e95e945fc167716fcd3a24fd6d7e7228b173d48623f5db6cc29d368751983", "save_bookmarks", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.storage.save_bookmarks")
        _result = _implementation(data_directory, bookmarks)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.storage.save_bookmarks"
        if _error.span is None:
            _error.span = {"end_byte":8199,"end_column":1,"end_line":194,"start_byte":7343,"start_column":1,"start_line":175}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.storage.save_bookmarks", phase="implementation-call", span={"end_byte":8199,"end_column":1,"end_line":194,"start_byte":7343,"start_column":1,"start_line":175}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.storage.save_bookmarks", phase="implementation-call", span={"end_byte":8199,"end_column":1,"end_line":194,"start_byte":7343,"start_column":1,"start_line":175}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[StoredFile, StoreError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="frogmouth.storage.save_bookmarks", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (StoreError_WriteFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="frogmouth.storage.save_bookmarks", phase="error", span={"end_byte":8199,"end_column":1,"end_line":194,"start_byte":7343,"start_column":1,"start_line":175}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="frogmouth.storage.save_bookmarks", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    if _expected_error_clause is not None:
        _cott_contract_condition(True, "frogmouth.storage.save_bookmarks", _expected_error_clause)
    if type(_result) is Err and type(_result.error) is StoreError_WriteFailed:
        _cott_contract_condition(True, "frogmouth.storage.save_bookmarks", "error:4")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            stored = _cott_match_value.value
            return (_cott_contract_condition(((_cott_starts_with((stored).path, data_directory) and _cott_ends_with((stored).path, "/bookmarks.json"))), "frogmouth.storage.save_bookmarks", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.storage.save_bookmarks", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.save_bookmarks", clause="ensures:2", phase="ensures", span={"end_byte":8043,"end_column":122,"end_line":187,"start_byte":7926,"start_column":5,"start_line":187}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Err and type(_cott_match_value.error) is StoreError_WriteFailed and True and True:
            path = getattr(_cott_match_value.error, _dataclasses.fields(type(_cott_match_value.error))[0].name)
            return (_cott_contract_condition((_cott_ends_with(path, "/bookmarks.json")), "frogmouth.storage.save_bookmarks", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.storage.save_bookmarks", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.save_bookmarks", clause="ensures:3", phase="ensures", span={"end_byte":8137,"end_column":94,"end_line":188,"start_byte":8048,"start_column":5,"start_line":188}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[StoredFile, StoreError], path="$.return", validator=_cott_validate_abi)
    return _result

def storage_failure_dialog(failure: StoreError) -> Dialog:
    """The error dialog reporting a failed application-data read or write.
PATH and MESSAGE are the fields of failure, escaped like rich.markup.escape
so they are shown literally. ReadFailed and Malformed have the title
"Unable to load application data"; WriteFailed has the title "Unable to
save application data". The message is PATH, two line feeds, MESSAGE and
a full stop."""
    failure = _cott_validate_abi(failure, StoreError, path="$.failure")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/storage/storage_failure_dialog.py", "c7bc4318b7352d76275d5bd1316f04526f8ce91ea443631167859a7f39cf0025", "storage_failure_dialog", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.storage.storage_failure_dialog")
        _result = _implementation(failure)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.storage.storage_failure_dialog"
        if _error.span is None:
            _error.span = {"end_byte":9225,"end_column":1,"end_line":212,"start_byte":8199,"start_column":1,"start_line":194}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.storage.storage_failure_dialog", phase="implementation-call", span={"end_byte":9225,"end_column":1,"end_line":212,"start_byte":8199,"start_column":1,"start_line":194}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.storage.storage_failure_dialog", phase="implementation-call", span={"end_byte":9225,"end_column":1,"end_line":212,"start_byte":8199,"start_column":1,"start_line":194}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Dialog, path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is StoreError_ReadFailed and True and True:
            return (_cott_contract_condition((((_result).title == "Unable to load application data")), "frogmouth.storage.storage_failure_dialog", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.storage.storage_failure_dialog", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.storage_failure_dialog", clause="ensures:1", phase="ensures", span={"end_byte":8783,"end_column":111,"end_line":204,"start_byte":8677,"start_column":5,"start_line":204}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is StoreError_Malformed and True and True:
            return (_cott_contract_condition((((_result).title == "Unable to load application data")), "frogmouth.storage.storage_failure_dialog", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.storage.storage_failure_dialog", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.storage_failure_dialog", clause="ensures:2", phase="ensures", span={"end_byte":8893,"end_column":110,"end_line":205,"start_byte":8788,"start_column":5,"start_line":205}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is StoreError_WriteFailed and True and True:
            return (_cott_contract_condition((((_result).title == "Unable to save application data")), "frogmouth.storage.storage_failure_dialog", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.storage.storage_failure_dialog", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.storage_failure_dialog", clause="ensures:3", phase="ensures", span={"end_byte":9005,"end_column":112,"end_line":206,"start_byte":8898,"start_column":5,"start_line":206}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = failure
        if type(_cott_match_value) is StoreError_WriteFailed and True and True:
            path = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition((((not ((not ("[" in path)) and (not ("\\" in path)))) or _cott_starts_with((_result).message, path))), "frogmouth.storage.storage_failure_dialog", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.storage.storage_failure_dialog", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.storage_failure_dialog", clause="ensures:4", phase="ensures", span={"end_byte":9162,"end_column":157,"end_line":207,"start_byte":9010,"start_column":5,"start_line":207}, expected="true", actual="false")
    if not (_cott_contract_condition((_cott_ends_with((_result).message, ".")), "frogmouth.storage.storage_failure_dialog", "ensures:5")):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.storage.storage_failure_dialog", clause="ensures:5", phase="ensures", span={"end_byte":9207,"end_column":45,"end_line":208,"start_byte":9167,"start_column":5,"start_line":208}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Dialog, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["LoadedBookmarks", "LoadedConfig", "StoreError", "StoreError_Malformed", "StoreError_ReadFailed", "StoreError_WriteFailed", "StoredFile", "load_bookmarks", "load_config", "load_history", "save_bookmarks", "save_config", "save_history", "storage_failure_dialog"]
