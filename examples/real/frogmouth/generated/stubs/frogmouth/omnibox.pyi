from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.omnibox_types import AddressAction as AddressAction, AddressAction_ChangeDirectory as AddressAction_ChangeDirectory, AddressAction_Failed as AddressAction_Failed, AddressAction_Ignore as AddressAction_Ignore, AddressAction_OpenExternally as AddressAction_OpenExternally, AddressAction_Quit as AddressAction_Quit, AddressAction_ResolveForge as AddressAction_ResolveForge, AddressAction_ShowAbout as AddressAction_ShowAbout, AddressAction_ShowHelp as AddressAction_ShowHelp, AddressAction_ShowPane as AddressAction_ShowPane, AddressAction_Visit as AddressAction_Visit, OmniboxCommand as OmniboxCommand, OmniboxCommand_About as OmniboxCommand_About, OmniboxCommand_Bookmarks as OmniboxCommand_Bookmarks, OmniboxCommand_ChangeDirectory as OmniboxCommand_ChangeDirectory, OmniboxCommand_Changelog as OmniboxCommand_Changelog, OmniboxCommand_Contents as OmniboxCommand_Contents, OmniboxCommand_Discord as OmniboxCommand_Discord, OmniboxCommand_Forge as OmniboxCommand_Forge, OmniboxCommand_Help as OmniboxCommand_Help, OmniboxCommand_History as OmniboxCommand_History, OmniboxCommand_Local as OmniboxCommand_Local, OmniboxCommand_Obsidian as OmniboxCommand_Obsidian, OmniboxCommand_Quit as OmniboxCommand_Quit
from frogmouth.document_types import BrowserFailure
from frogmouth.layout_types import Pane
from frogmouth.model_types import Forge, Location, LocationKind, LocationKind_Local, LocationKind_Remote
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
def parse_command(value: str) -> Option[OmniboxCommand]: ...

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
def interpret_address(value: str, home: str, working_directory: str) -> AddressAction: ...

__all__ = ["AddressAction", "AddressAction_ChangeDirectory", "AddressAction_Failed", "AddressAction_Ignore", "AddressAction_OpenExternally", "AddressAction_Quit", "AddressAction_ResolveForge", "AddressAction_ShowAbout", "AddressAction_ShowHelp", "AddressAction_ShowPane", "AddressAction_Visit", "OmniboxCommand", "OmniboxCommand_About", "OmniboxCommand_Bookmarks", "OmniboxCommand_ChangeDirectory", "OmniboxCommand_Changelog", "OmniboxCommand_Contents", "OmniboxCommand_Discord", "OmniboxCommand_Forge", "OmniboxCommand_Help", "OmniboxCommand_History", "OmniboxCommand_Local", "OmniboxCommand_Obsidian", "OmniboxCommand_Quit", "interpret_address", "parse_command"]
