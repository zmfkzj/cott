from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.document_types import BrowserFailure as BrowserFailure, BrowserFailure_DoesNotExist as BrowserFailure_DoesNotExist, BrowserFailure_ForgeUnresolved as BrowserFailure_ForgeUnresolved, BrowserFailure_Load as BrowserFailure_Load, BrowserFailure_NoSuchDirectory as BrowserFailure_NoSuchDirectory, BrowserFailure_NotADirectory as BrowserFailure_NotADirectory, BrowserFailure_NotBookmarkable as BrowserFailure_NotBookmarkable, BrowserFailure_UnhandledLink as BrowserFailure_UnhandledLink, LinkAction as LinkAction, LinkAction_Anchor as LinkAction_Anchor, LinkAction_Failed as LinkAction_Failed, LinkAction_OpenExternally as LinkAction_OpenExternally, LinkAction_Visit as LinkAction_Visit, LoadError as LoadError, LoadError_LocalFailed as LoadError_LocalFailed, LoadError_RemoteFailed as LoadError_RemoteFailed, RemoteDocument as RemoteDocument, RemoteDocument_Markdown as RemoteDocument_Markdown, RemoteDocument_NotMarkdown as RemoteDocument_NotMarkdown, VisitOutcome as VisitOutcome, VisitOutcome_Failed as VisitOutcome_Failed, VisitOutcome_Loaded as VisitOutcome_Loaded, VisitOutcome_OpenExternally as VisitOutcome_OpenExternally
from frogmouth.model_types import BrowserContext, Dialog, Document, Forge, Forge_BitBucket, Forge_Codeberg, Forge_GitHub, Forge_GitLab, Location, LocationKind, LocationKind_Local, LocationKind_Remote
"""Read the Markdown file at path from the file system the program runs
against: the fs fixture root while a Cott scenario with an fs fixture is
active, otherwise the host file system, where a relative path is relative
to the process working directory. The bytes are decoded as UTF-8, with
each invalid sequence replaced by U+FFFD as the remote loader does, so a
file that is not UTF-8 still loads; each "\\r\\n" or lone "\\r" line ending
becomes "\\n", as Python's universal-newline text reading does; nothing
else changes. The document's location is the Local location path. A
failure to open or read the file, a directory included, is
LocalFailed(path, the error text as Python's str() renders the OSError)."""
def load_local_document(path: str) -> Result[Document, LoadError]: ...

"""GET url with the header "User-Agent: frogmouth v0.9.1", following
redirects, with a 5 second timeout for connecting and for each read. A
transport failure (name resolution, connection, timeout, redirect loop or
malformed response) is RemoteFailed(url, a description of the failure).
A final status outside 200-299 is RemoteFailed(url, MESSAGE), where
MESSAGE is "KIND 'STATUS REASON' for url 'FINAL'\\nFor more information
check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/STATUS"
with KIND "Informational response" (1xx), "Redirect response" (3xx),
"Client error" (4xx), "Server error" (5xx) or "Invalid status code",
REASON the response's reason phrase and FINAL the URL of the final
request.

On success the Content-Type header, empty when absent, decides. A value
starting with "text/plain", "text/markdown" or "text/x-markdown" gives
Markdown of the document at the Remote location url, whose markdown is
the body decoded with the Content-Type charset parameter when it names a
known codec and UTF-8 otherwise, replacing undecodable bytes with U+FFFD.
Any other value gives NotMarkdown of that value."""
def fetch_remote_document(url: str) -> Result[RemoteDocument, LoadError]: ...

"""Visit location the way the viewer does.

When frogmouth.locations.is_markdown_location(location,
context.markdown_extensions) holds, a Local location is loaded with
frogmouth.document.load_local_document of PATH, where PATH is
frogmouth.locations.resolve_local_path(location.target, context.home,
context.working_directory); a Remote location is fetched with
frogmouth.document.fetch_remote_document(location.target). A loaded
Markdown document is Loaded; NotMarkdown is OpenExternally of
location.target; a LoadError is Failed(Load(error)).

Any other Remote location is OpenExternally of its target without a
request. Any other Local location is classified with
frogmouth.locations.inspect_local_path(PATH): Missing is
Failed(DoesNotExist(location.target)), any other kind is OpenExternally
of "file://" followed by PATH."""
def visit_location(location: Location, context: BrowserContext) -> VisitOutcome: ...

"""Decide where a clicked Markdown link leads. href is already
percent-decoded; current is the location being viewed, if any.

1. An href starting with "#" is Anchor of the rest of href.
2. Otherwise split href at its first "#" into BASE and FRAGMENT. ANCHOR
   is FRAGMENT when href has a "#" and FRAGMENT is not empty, otherwise
   Nothing.
3. When frogmouth.locations.remote_location(BASE) is a location, Visit
   it with ANCHOR.
4. When current is a Remote location, resolve BASE against its target
   as an RFC 3986 reference, as Python urllib.parse.urljoin does. A
   result that remote_location recognizes is Visit of that location with
   ANCHOR; any other result is OpenExternally of it.
5. Otherwise, when frogmouth.locations.normalize_local_path(
   context.working_directory, BASE) is not Missing according to
   frogmouth.locations.inspect_local_path, Visit that Local path with
   ANCHOR.
6. Otherwise, when current is a Local location, let DIR be
   normalize_local_path(context.working_directory, current.target)
   without its last segment and separating "/" ("/" when only the root
   remains, "." when nothing remains). When normalize_local_path(DIR,
   BASE) is not Missing, Visit that Local path with ANCHOR.
7. Otherwise the result is Failed(UnhandledLink(href))."""
def resolve_link(href: str, current: Option[Location], context: BrowserContext) -> LinkAction: ...

"""Filter a directory listing of non-empty paths for the local file
browser, keeping the given order. A path is kept when its name (last
"/"-separated segment) does not start with "." and
frogmouth.locations.inspect_local_path says Directory, or when
inspect_local_path says File and frogmouth.locations.is_markdown_location
of the Local location path holds for extensions, so Markdown files are
kept even when hidden."""
def select_browsable_entries(paths: CottList[str], extensions: CottList[str]) -> CottList[str]: ...

"""Ask the desktop to open target, a web, mail or file URL, with its default
application: start the opener program ("open" on macOS, "xdg-open"
elsewhere) with target as its only argument, standard input, output and
error on the null device, in a new session, without waiting for it. The
result is true when the opener process started and false when it could
not be started (for example because the program is not installed)."""
def open_external(target: str) -> bool: ...

"""The error dialog that reports failure. Every interpolated value (PATH,
HREF, URL, MESSAGE) is escaped like rich.markup.escape so it is shown
literally; FORGE is "GitHub", "GitLab", "BitBucket" or "Codeberg".

DoesNotExist(PATH): "Does not exist" / "Unable to open PATH because it
does not exist."
NoSuchDirectory(PATH): "No such directory" / "PATH does not exist."
NotADirectory(PATH): "Not a directory" / "PATH is not a directory."
ForgeUnresolved(FORGE): "Unable to work out a FORGE URL" / "After trying
a few options it hasn't been possible to work out the FORGE URL.\\n\\n
Perhaps the file you're after is on an unusual branch, or the spelling is
wrong?" (the two paragraphs are separated by exactly "\\n\\n").
UnhandledLink(HREF): "Unable to handle link" / "Unable to work out how to
handle this link:\\n\\nHREF"
NotBookmarkable: "Not a bookmarkable location" / "The current view can't
be bookmarked."
Load(LocalFailed(PATH, MESSAGE)): "Error loading local document" /
"PATH\\n\\nMESSAGE."
Load(RemoteFailed(URL, MESSAGE)): "Error getting document" / "MESSAGE"
Titles and messages contain nothing else."""
def failure_dialog(failure: BrowserFailure) -> Dialog: ...

__all__ = ["BrowserFailure", "BrowserFailure_DoesNotExist", "BrowserFailure_ForgeUnresolved", "BrowserFailure_Load", "BrowserFailure_NoSuchDirectory", "BrowserFailure_NotADirectory", "BrowserFailure_NotBookmarkable", "BrowserFailure_UnhandledLink", "LinkAction", "LinkAction_Anchor", "LinkAction_Failed", "LinkAction_OpenExternally", "LinkAction_Visit", "LoadError", "LoadError_LocalFailed", "LoadError_RemoteFailed", "RemoteDocument", "RemoteDocument_Markdown", "RemoteDocument_NotMarkdown", "VisitOutcome", "VisitOutcome_Failed", "VisitOutcome_Loaded", "VisitOutcome_OpenExternally", "failure_dialog", "fetch_remote_document", "load_local_document", "open_external", "resolve_link", "select_browsable_entries", "visit_location"]
