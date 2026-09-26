from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.storage_types import LoadedBookmarks as LoadedBookmarks, LoadedConfig as LoadedConfig, StoreError as StoreError, StoreError_Malformed as StoreError_Malformed, StoreError_ReadFailed as StoreError_ReadFailed, StoreError_WriteFailed as StoreError_WriteFailed, StoredFile as StoredFile
from frogmouth.bookmarks_types import Bookmark
from frogmouth.config_types import Config
from frogmouth.history_types import History
from frogmouth.model_types import Dialog, Location
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
def load_config(config_directory: str) -> Result[LoadedConfig, StoreError]: ...

"""Store config as configuration.json in config_directory, creating missing
directories. The content is the JSON object with the keys "light_mode"
(true for Light), "markdown_extensions" and "navigation_left" (true for
Left) in that order, serialized like Python json.dumps with indent=4 and
the default ASCII escaping, without a trailing newline. The file is
replaced atomically, so a failed save leaves the previous file intact,
and every failure is WriteFailed carrying the file path."""
def save_config(config_directory: str, config: Config) -> Result[StoredFile, StoreError]: ...

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
def load_history(data_directory: str) -> Result[History, StoreError]: ...

"""Store locations as history.json in data_directory, creating missing
directories: a JSON array of the location targets in order, serialized
like Python json.dumps with indent=4 and the default ASCII escaping,
without a trailing newline. The file is replaced atomically, so a failed
save leaves the previous file intact, and every failure is WriteFailed
carrying the file path."""
def save_history(data_directory: str, locations: CottList[Location]) -> Result[StoredFile, StoreError]: ...

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
def load_bookmarks(data_directory: str) -> Result[LoadedBookmarks, StoreError]: ...

"""Store bookmarks as bookmarks.json in data_directory, creating missing
directories: a JSON array holding [title, target] for each bookmark in
order, serialized like Python json.dumps with indent=4 and the default
ASCII escaping, without a trailing newline. The file is replaced
atomically, so a failed save leaves the previous file intact, and every
failure is WriteFailed carrying the file path."""
def save_bookmarks(data_directory: str, bookmarks: CottList[Bookmark]) -> Result[StoredFile, StoreError]: ...

"""The error dialog reporting a failed application-data read or write.
PATH and MESSAGE are the fields of failure, escaped like rich.markup.escape
so they are shown literally. ReadFailed and Malformed have the title
"Unable to load application data"; WriteFailed has the title "Unable to
save application data". The message is PATH, two line feeds, MESSAGE and
a full stop."""
def storage_failure_dialog(failure: StoreError) -> Dialog: ...

__all__ = ["LoadedBookmarks", "LoadedConfig", "StoreError", "StoreError_Malformed", "StoreError_ReadFailed", "StoreError_WriteFailed", "StoredFile", "load_bookmarks", "load_config", "load_history", "save_bookmarks", "save_config", "save_history", "storage_failure_dialog"]
