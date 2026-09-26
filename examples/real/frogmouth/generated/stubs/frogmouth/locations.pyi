from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit
from frogmouth.model_types import Location, LocationKind, LocationKind_Remote, PathKind
"""Recognize text that is likely a web URL, the way the address bar, links
and stored locations are classified. candidate is not trimmed. It is a URL
when its scheme, the text before the first "://", is "http" or "https"
compared ASCII case-insensitively, and its authority, the text after that
"://" up to the first "/", "?" or "#", still names a non-empty host once a
leading "userinfo@" part and a trailing ":port" part are removed. Nothing
else is validated. The Remote target is candidate with its scheme
lower-cased and every other character unchanged. Any other candidate,
including "http://", "ftp://host/a.md" and "example.com/a.md", is Nothing."""
def remote_location(candidate: str) -> Option[Location]: ...

"""Lexically resolve path against directory without consulting the file
system. A path starting with "/" stands alone; an empty path names
directory; any other path is appended to directory after one "/". The
combined text is split at "/": empty and "." segments are dropped, and a
".." segment removes the nearest preceding kept segment, or is dropped
when there is none. The kept segments are joined with "/", with a leading
"/" when the combined text started with one. An absolute result without
segments is "/"; a relative result without segments is ".". Symbolic links
are not resolved and "~" has no special meaning."""
def normalize_local_path(directory: str, path: str) -> str: ...

"""The local path that address-bar or command text names: pathlib's
expanduser() followed by lexical absolutization. Text that is exactly "~"
becomes home and a leading "~/" becomes home followed by "/"; text starting
with "~" otherwise (such as "~user/a.md") is kept literally. The result is
frogmouth.locations.normalize_local_path(working_directory, expanded text)."""
def resolve_local_path(text: str, home: str, working_directory: str) -> str: ...

"""Classify path in the file system the program runs against, following
symbolic links: the fs fixture root while a Cott scenario with an fs
fixture is active, otherwise the host file system, where a relative path
is relative to the process working directory. File is a regular file, Directory a directory, Other any other
existing kind (FIFO, socket, device). Missing means the path does not
exist or cannot be examined: an absent entry, a non-directory component,
a symbolic-link loop or denied permission."""
def inspect_local_path(path: str) -> PathKind: ...

"""Whether location looks like a Markdown document by its suffix. The name is
the last "/"-separated segment, ignoring trailing "/" characters, of the
Local target or of the Remote URL's path (the text after the authority up
to the first "?" or "#"). With the name's leading "." characters removed,
the suffix is the text from its last "." to the end, or empty when there
is none; so ".md" has no suffix, "a." has the suffix "." and
"archive.tar.gz" has ".gz". The result is true exactly when the ASCII
lower-cased suffix is one of extensions, compared exactly."""
def is_markdown_location(location: Location, extensions: CottList[str]) -> bool: ...

__all__ = ["inspect_local_path", "is_markdown_location", "normalize_local_path", "remote_location", "resolve_local_path"]
