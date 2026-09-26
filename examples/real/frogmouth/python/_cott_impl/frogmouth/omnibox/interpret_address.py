from typing import Final

from cott_runtime import Nothing, Some
from frogmouth.forge import forge_candidate_urls, parse_forge_request
from frogmouth.locations import inspect_local_path, remote_location, resolve_local_path
from frogmouth.omnibox import parse_command
from frogmouth.document_types import BrowserFailure_NoSuchDirectory, BrowserFailure_NotADirectory
from frogmouth.layout_types import Pane_Bookmarks, Pane_Contents, Pane_History, Pane_Local
from frogmouth.model_types import ForgeRequest, Forge_GitHub, Location, LocationKind_Local, PathKind_Directory, PathKind_File, PathKind_Missing
from frogmouth.omnibox_types import AddressAction, AddressAction_ChangeDirectory, AddressAction_Failed, AddressAction_Ignore, AddressAction_OpenExternally, AddressAction_Quit, AddressAction_ResolveForge, AddressAction_ShowAbout, AddressAction_ShowHelp, AddressAction_ShowPane, AddressAction_Visit, OmniboxCommand_About, OmniboxCommand_Bookmarks, OmniboxCommand_ChangeDirectory, OmniboxCommand_Changelog, OmniboxCommand_Contents, OmniboxCommand_Discord, OmniboxCommand_Forge, OmniboxCommand_Help, OmniboxCommand_History, OmniboxCommand_Local, OmniboxCommand_Quit

_DISCORD: Final[str] = "https://discord.gg/Enf6Z3qhVr"
_OBSIDIAN: Final[str] = "/Library/Mobile Documents/iCloud~md~obsidian/Documents"


def _change_directory(target: str, home: str, working_directory: str) -> AddressAction:
    path = resolve_local_path(target if target else "~", home, working_directory)
    kind = inspect_local_path(path)
    if isinstance(kind, PathKind_Directory):
        return AddressAction_ChangeDirectory(path=path)
    if isinstance(kind, PathKind_Missing):
        return AddressAction_Failed(failure=BrowserFailure_NoSuchDirectory(path=path))
    return AddressAction_Failed(failure=BrowserFailure_NotADirectory(path=path))


def interpret_address(value: str, home: str, working_directory: str) -> AddressAction:
    text = value.strip()
    remote = remote_location(text)
    if isinstance(remote, Some):
        return AddressAction_Visit(location=remote.value, address="")
    path = resolve_local_path(text, home, working_directory)
    kind = inspect_local_path(path)
    if isinstance(kind, PathKind_File):
        return AddressAction_Visit(location=Location(kind=LocationKind_Local(), target=path), address=path)
    if isinstance(kind, PathKind_Directory):
        return AddressAction_ChangeDirectory(path=path)
    if not isinstance(kind, PathKind_Missing):
        return AddressAction_Ignore()
    parsed = parse_command(text)
    if isinstance(parsed, Some):
        command = parsed.value
        if isinstance(command, OmniboxCommand_About):
            return AddressAction_ShowAbout()
        if isinstance(command, OmniboxCommand_Help):
            return AddressAction_ShowHelp()
        if isinstance(command, OmniboxCommand_Quit):
            return AddressAction_Quit()
        if isinstance(command, OmniboxCommand_Contents):
            return AddressAction_ShowPane(pane=Pane_Contents())
        if isinstance(command, OmniboxCommand_Local):
            return AddressAction_ShowPane(pane=Pane_Local())
        if isinstance(command, OmniboxCommand_Bookmarks):
            return AddressAction_ShowPane(pane=Pane_Bookmarks())
        if isinstance(command, OmniboxCommand_History):
            return AddressAction_ShowPane(pane=Pane_History())
        if isinstance(command, OmniboxCommand_Discord):
            return AddressAction_OpenExternally(target=_DISCORD)
        if isinstance(command, OmniboxCommand_Changelog):
            request = ForgeRequest(owner="textualize", repository="frogmouth", branch=Nothing(), file=Some(value="ChangeLog.md"))
            return AddressAction_ResolveForge(forge=Forge_GitHub(), candidates=forge_candidate_urls(Forge_GitHub(), request))
        if isinstance(command, OmniboxCommand_Forge):
            forge_request = parse_forge_request(command.arguments)
            if isinstance(forge_request, Some):
                return AddressAction_ResolveForge(forge=command.forge, candidates=forge_candidate_urls(command.forge, forge_request.value))
            return AddressAction_Ignore()
        if isinstance(command, OmniboxCommand_ChangeDirectory):
            return _change_directory(command.target, home, working_directory)
        vault = home + _OBSIDIAN
        if command.vault:
            vault = vault + "/" + command.vault
        if isinstance(inspect_local_path(vault), PathKind_Missing):
            return AddressAction_Ignore()
        return _change_directory(vault, home, working_directory)
    if text:
        return AddressAction_Visit(location=Location(kind=LocationKind_Local(), target=text), address=text)
    return AddressAction_Ignore()
