from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from frogmouth.model_types import Forge, ForgeRequest, Location, LocationKind, LocationKind_Remote

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ForgeError_Unresolved:
    __hash__ = None
    forge: Forge

ForgeError: TypeAlias = Union[ForgeError_Unresolved]

"""Parse the arguments of a forge quick-view command. Leading and trailing
whitespace is removed as Python str.strip() does, then two Python regular
expressions are tried in order and the first that matches decides:

^(?P<owner>[^/ ]+)[/ ](?P<repo>[^ :]+)(?: +(?P<file>[^ ]+))?$
^(?P<owner>[^/ ]+)[/ ](?P<repo>[^ :]+):(?P<branch>[^ ]+)(?: +(?P<file>[^ ]+))?$

owner and repository are the owner and repo groups; branch and file are
the groups of those names, Nothing when they did not participate (the
first expression has no branch). Text neither expression matches is
Nothing."""
"""The raw-file URLs to probe, one per branch in probing order: request's
branch alone when it has one, otherwise "main" then "master". FILE is
request.file, or "README.md" when it has none. OWNER, REPOSITORY, BRANCH
and FILE are substituted verbatim into the forge's pattern:

GitHub:    https://raw.githubusercontent.com/OWNER/REPOSITORY/BRANCH/FILE
GitLab:    https://gitlab.com/OWNER/REPOSITORY/-/raw/BRANCH/FILE
BitBucket: https://bitbucket.org/OWNER/REPOSITORY/raw/BRANCH/FILE
Codeberg:  https://codeberg.org/OWNER/REPOSITORY/raw//branch/BRANCH/FILE"""
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
__all__ = ["ForgeError", "ForgeError_Unresolved"]
