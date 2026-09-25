from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.document_types import LoadError as LoadError, LoadError_InvalidEncoding as LoadError_InvalidEncoding, LoadError_NetworkFailed as LoadError_NetworkFailed, LoadError_NotFound as LoadError_NotFound, LoadError_ReadFailed as LoadError_ReadFailed, LoadError_TooLarge as LoadError_TooLarge, OpenError as OpenError, OpenError_Load as OpenError_Load, OpenError_Navigation as OpenError_Navigation
from frogmouth.model_types import Document, Location, LocationKind, LocationKind_Http, LocationKind_Local
from frogmouth.navigation_types import NavigationError
"""Choose a document title. Split markdown into lines at LF and remove one
trailing CR from each. A heading line starts with a run of one to six "#"
characters (the whole leading run) followed by a space; its text is the rest
of the line with leading and trailing spaces and tabs removed. The title is
the text of the first heading line whose text is non-empty. Without one, the
title is the last non-empty "/"-separated segment of location.target, or
location.target itself when it has no non-empty segment. Only this line rule
applies: code blocks, setext headings and inline markup are not interpreted."""
def derive_title(location: Location, markdown: str) -> str: ...

"""Load Markdown for location, reading at most 5242880 bytes (5 MiB) plus one
byte to detect a larger document.

Local: read the file at location.target from the file system the program
runs against: the fs fixture root while a Cott scenario with an fs fixture
is active, otherwise the host file system, where a relative target is
relative to the process working directory. A missing file is NotFound; any
other open or read failure is ReadFailed. While a scenario fs fixture is
active, a target the fixture does not permit (absolute, or outside the
fixture root) is a contract violation raised by the fixture, not a read
failure.

Http: send one GET to location.target, following redirects, with a 30000
millisecond timeout for the connection attempt and each blocking read. A
final status of 404 or 410 is NotFound. Any other final status outside
200-299 is NetworkFailed whose message contains the decimal status. Name
resolution, connection, timeout and incomplete-response failures are
NetworkFailed.

More than 5242880 bytes is TooLarge. Bytes that are not strict UTF-8 are
InvalidEncoding. The markdown is the decoded text with one leading U+FEFF
removed, otherwise unchanged, and the title is
frogmouth.document.derive_title(location, markdown). Every LoadError's
source is location.target."""
def load_document(location: Location) -> Result[Document, LoadError]: ...

"""The frogmouth composition root, used by the address bar and by reload. Call
frogmouth.navigation.resolve_location(value, working_directory); its error is
returned as OpenError.Navigation and nothing is loaded. Otherwise return
frogmouth.document.load_document of the resolved location, with its error
returned as OpenError.Load."""
def open_location(value: str, working_directory: Path) -> Result[Document, OpenError]: ...

__all__ = ["LoadError", "LoadError_InvalidEncoding", "LoadError_NetworkFailed", "LoadError_NotFound", "LoadError_ReadFailed", "LoadError_TooLarge", "OpenError", "OpenError_Load", "OpenError_Navigation", "derive_title", "load_document", "open_location"]
