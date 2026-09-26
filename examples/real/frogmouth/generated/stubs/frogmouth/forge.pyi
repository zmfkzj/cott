from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.forge_types import ForgeError as ForgeError, ForgeError_Unresolved as ForgeError_Unresolved
from frogmouth.model_types import Forge, ForgeRequest, Location, LocationKind, LocationKind_Remote
"""Parse the arguments of a forge quick-view command. Leading and trailing
whitespace is removed as Python str.strip() does, then two Python regular
expressions are tried in order and the first that matches decides:

^(?P<owner>[^/ ]+)[/ ](?P<repo>[^ :]+)(?: +(?P<file>[^ ]+))?$
^(?P<owner>[^/ ]+)[/ ](?P<repo>[^ :]+):(?P<branch>[^ ]+)(?: +(?P<file>[^ ]+))?$

owner and repository are the owner and repo groups; branch and file are
the groups of those names, Nothing when they did not participate (the
first expression has no branch). Text neither expression matches is
Nothing."""
def parse_forge_request(arguments: str) -> Option[ForgeRequest]: ...

"""The raw-file URLs to probe, one per branch in probing order: request's
branch alone when it has one, otherwise "main" then "master". FILE is
request.file, or "README.md" when it has none. OWNER, REPOSITORY, BRANCH
and FILE are substituted verbatim into the forge's pattern:

GitHub:    https://raw.githubusercontent.com/OWNER/REPOSITORY/BRANCH/FILE
GitLab:    https://gitlab.com/OWNER/REPOSITORY/-/raw/BRANCH/FILE
BitBucket: https://bitbucket.org/OWNER/REPOSITORY/raw/BRANCH/FILE
Codeberg:  https://codeberg.org/OWNER/REPOSITORY/raw//branch/BRANCH/FILE"""
def forge_candidate_urls(forge: Forge, request: ForgeRequest) -> CottList[str]: ...

"""Find the first candidate URL that exists. Every candidate is an http or
https URL. Candidates are probed in order with an HTTP HEAD request
carrying the header "User-Agent: frogmouth v0.9.1", following redirects,
with a 5 second timeout for connecting and for each read; a server that
answers the HEAD request with status 405 or 501 is asked once more for
the same candidate with GET. The first candidate whose final status is
200-299 is returned as a Remote location whose target is that candidate
(not the redirect target). Any other final status moves on to the next
candidate. A transport failure (name resolution, connection, timeout or
a malformed response) ends probing at once. When probing ends without a
found candidate the result is Unresolved(forge)."""
def locate_forge_file(forge: Forge, candidates: CottList[str]) -> Result[Location, ForgeError]: ...

__all__ = ["ForgeError", "ForgeError_Unresolved", "forge_candidate_urls", "locate_forge_file", "parse_forge_request"]
