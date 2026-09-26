from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from frogmouth.document_types import BrowserFailure
from frogmouth.layout_types import Pane
from frogmouth.model_types import Forge, Location, LocationKind, LocationKind_Local, LocationKind_Remote

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OmniboxCommand_About:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OmniboxCommand_Bookmarks:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OmniboxCommand_Changelog:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OmniboxCommand_ChangeDirectory:
    __hash__ = None
    target: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OmniboxCommand_Contents:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OmniboxCommand_Discord:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OmniboxCommand_Forge:
    __hash__ = None
    forge: Forge
    arguments: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OmniboxCommand_Help:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OmniboxCommand_History:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OmniboxCommand_Local:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OmniboxCommand_Obsidian:
    __hash__ = None
    vault: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OmniboxCommand_Quit:
    pass

OmniboxCommand: TypeAlias = Union[OmniboxCommand_About, OmniboxCommand_Bookmarks, OmniboxCommand_Changelog, OmniboxCommand_ChangeDirectory, OmniboxCommand_Contents, OmniboxCommand_Discord, OmniboxCommand_Forge, OmniboxCommand_Help, OmniboxCommand_History, OmniboxCommand_Local, OmniboxCommand_Obsidian, OmniboxCommand_Quit]

"""What submitting the address bar asks the browser to do. address is the text
the address bar shows right after a Visit; every other action empties it."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AddressAction_Visit:
    __hash__ = None
    location: Location
    address: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AddressAction_ChangeDirectory:
    __hash__ = None
    path: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AddressAction_ResolveForge:
    __hash__ = None
    forge: Forge
    candidates: CottList[str]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AddressAction_OpenExternally:
    __hash__ = None
    target: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AddressAction_ShowPane:
    __hash__ = None
    pane: Pane

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AddressAction_ShowHelp:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AddressAction_ShowAbout:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AddressAction_Quit:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AddressAction_Failed:
    __hash__ = None
    failure: BrowserFailure

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AddressAction_Ignore:
    pass

AddressAction: TypeAlias = Union[AddressAction_Visit, AddressAction_ChangeDirectory, AddressAction_ResolveForge, AddressAction_OpenExternally, AddressAction_ShowPane, AddressAction_ShowHelp, AddressAction_ShowAbout, AddressAction_Quit, AddressAction_Failed, AddressAction_Ignore]

"""Recognize an address-bar command. value is split like Python
str.split(None, 1) into a command word and the rest; the arguments are
the rest with surrounding whitespace removed (empty when there is none).
The word is compared after ASCII lower-casing, while the arguments keep
their case. Aliases name commands: "a" about, "b" and "bm" bookmarks,
"bb" bitbucket, "c" and "toc" contents, "cb" codeberg, "cd" chdir, "cl"
changelog, "gh" github, "gl" gitlab, "h" history, "l" local, "obs"
obsidian, "q" quit and "?" help. The commands are about, bookmarks,
changelog, contents, discord, help, history, local and quit, which ignore
arguments; chdir (ChangeDirectory with the arguments as target);
obsidian (Obsidian with the arguments as vault); and github, gitlab,
bitbucket and codeberg (Forge of GitHub, GitLab, BitBucket or Codeberg
with the arguments). Any other word, or a value without a word, is
Nothing."""
"""Decide what the submitted address-bar text asks for. Let TEXT be value
with surrounding whitespace removed as Python str.strip() does.

1. When frogmouth.locations.remote_location(TEXT) is a location, Visit
   it with address "".
2. Otherwise let PATH be frogmouth.locations.resolve_local_path(TEXT,
   home, working_directory) and classify it with
   frogmouth.locations.inspect_local_path. A File is Visit of the Local
   location PATH with address PATH; a Directory is ChangeDirectory(PATH);
   Other is Ignore.
3. When PATH is Missing and frogmouth.omnibox.parse_command(TEXT) is a
   command: about is ShowAbout; help is ShowHelp; quit is Quit;
   contents, local, bookmarks and history are ShowPane of the Contents,
   Local, Bookmarks and History pane; discord is OpenExternally of
   "https://discord.gg/Enf6Z3qhVr"; changelog is ResolveForge(GitHub,
   frogmouth.forge.forge_candidate_urls of owner "textualize",
   repository "frogmouth", no branch and file "ChangeLog.md"). A forge
   command whose arguments frogmouth.forge.parse_forge_request parses is
   ResolveForge(forge, forge_candidate_urls(forge, request)); otherwise
   it is Ignore. chdir resolves its target, or "~" when the target is
   empty, with resolve_local_path and classifies the result: a Directory
   is ChangeDirectory of it, a Missing path is
   Failed(NoSuchDirectory(it)) and any other kind
   Failed(NotADirectory(it)). obsidian names the directory home followed
   by "/Library/Mobile Documents/iCloud~md~obsidian/Documents" and, when
   the vault is not empty, "/" and the vault; when that path is not
   Missing it is handled as chdir of it, otherwise the result is Ignore.
4. Any other non-empty TEXT is Visit of the Local location TEXT, not
   resolved, with address TEXT, so a mistyped name is reported by the
   visit; an empty TEXT here is Ignore."""
__all__ = ["AddressAction", "AddressAction_ChangeDirectory", "AddressAction_Failed", "AddressAction_Ignore", "AddressAction_OpenExternally", "AddressAction_Quit", "AddressAction_ResolveForge", "AddressAction_ShowAbout", "AddressAction_ShowHelp", "AddressAction_ShowPane", "AddressAction_Visit", "OmniboxCommand", "OmniboxCommand_About", "OmniboxCommand_Bookmarks", "OmniboxCommand_ChangeDirectory", "OmniboxCommand_Changelog", "OmniboxCommand_Contents", "OmniboxCommand_Discord", "OmniboxCommand_Forge", "OmniboxCommand_Help", "OmniboxCommand_History", "OmniboxCommand_Local", "OmniboxCommand_Obsidian", "OmniboxCommand_Quit"]
