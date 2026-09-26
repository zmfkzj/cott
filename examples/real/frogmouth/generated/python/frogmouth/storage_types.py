from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from frogmouth.bookmarks_types import Bookmark
from frogmouth.config_types import Config
from frogmouth.history_types import History
from frogmouth.model_types import Dialog, Location

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StoreError_ReadFailed:
    __hash__ = None
    path: str
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StoreError_Malformed:
    __hash__ = None
    path: str
    message: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StoreError_WriteFailed:
    __hash__ = None
    path: str
    message: str

StoreError: TypeAlias = Union[StoreError_ReadFailed, StoreError_Malformed, StoreError_WriteFailed]

"""Proof of a completed application-data write: the file that now holds the data
and the number of UTF-8 bytes written to it."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StoredFile:
    __hash__ = None
    path: str
    bytes_written: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, str, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "bytes_written", _cott_validate_abi(self.bytes_written, U64, path="$.bytes_written"))
        if not (_cott_contract_condition(((len((self).path) > 0)), "frogmouth.storage.StoredFile", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.storage.StoredFile", clause="invariant:0", phase="invariant", span={"end_byte":551,"end_column":32,"end_line":21,"start_byte":524,"start_column":5,"start_line":21}, expected="true", actual="false")
        if not (_cott_contract_condition((((self).bytes_written > 0)), "frogmouth.storage.StoredFile", "invariant:1")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.storage.StoredFile", clause="invariant:1", phase="invariant", span={"end_byte":588,"end_column":37,"end_line":22,"start_byte":556,"start_column":5,"start_line":22}, expected="true", actual="false")

"""A configuration read by load_config and the configuration file it came from."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LoadedConfig:
    __hash__ = None
    path: str
    config: Config

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, str, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "config", _cott_validate_abi(self.config, Config, path="$.config"))
        if not (_cott_contract_condition((_cott_ends_with((self).path, "/configuration.json")), "frogmouth.storage.LoadedConfig", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.storage.LoadedConfig", clause="invariant:0", phase="invariant", span={"end_byte":791,"end_column":58,"end_line":31,"start_byte":738,"start_column":5,"start_line":31}, expected="true", actual="false")

"""Bookmarks read by load_bookmarks, in stored order, and the bookmarks file
they came from."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LoadedBookmarks:
    __hash__ = None
    path: str
    bookmarks: CottList[Bookmark]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "path", _cott_validate_abi(self.path, str, path="$.path"))
        if not _cott_validated_construction():
            object.__setattr__(self, "bookmarks", _cott_validate_abi(self.bookmarks, CottList[Bookmark], path="$.bookmarks"))
        if not (_cott_contract_condition((_cott_ends_with((self).path, "/bookmarks.json")), "frogmouth.storage.LoadedBookmarks", "invariant:0")):
            raise CottContractViolation("invariant failed", symbol="frogmouth.storage.LoadedBookmarks", clause="invariant:0", phase="invariant", span={"end_byte":1017,"end_column":54,"end_line":41,"start_byte":968,"start_column":5,"start_line":41}, expected="true", actual="false")

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
"""Store config as configuration.json in config_directory, creating missing
directories. The content is the JSON object with the keys "light_mode"
(true for Light), "markdown_extensions" and "navigation_left" (true for
Left) in that order, serialized like Python json.dumps with indent=4 and
the default ASCII escaping, without a trailing newline. The file is
replaced atomically, so a failed save leaves the previous file intact,
and every failure is WriteFailed carrying the file path."""
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
"""Store locations as history.json in data_directory, creating missing
directories: a JSON array of the location targets in order, serialized
like Python json.dumps with indent=4 and the default ASCII escaping,
without a trailing newline. The file is replaced atomically, so a failed
save leaves the previous file intact, and every failure is WriteFailed
carrying the file path."""
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
"""Store bookmarks as bookmarks.json in data_directory, creating missing
directories: a JSON array holding [title, target] for each bookmark in
order, serialized like Python json.dumps with indent=4 and the default
ASCII escaping, without a trailing newline. The file is replaced
atomically, so a failed save leaves the previous file intact, and every
failure is WriteFailed carrying the file path."""
"""The error dialog reporting a failed application-data read or write.
PATH and MESSAGE are the fields of failure, escaped like rich.markup.escape
so they are shown literally. ReadFailed and Malformed have the title
"Unable to load application data"; WriteFailed has the title "Unable to
save application data". The message is PATH, two line feeds, MESSAGE and
a full stop."""
__all__ = ["LoadedBookmarks", "LoadedConfig", "StoreError", "StoreError_Malformed", "StoreError_ReadFailed", "StoreError_WriteFailed", "StoredFile"]
