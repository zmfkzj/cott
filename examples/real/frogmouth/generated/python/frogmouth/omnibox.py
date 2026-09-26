from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from frogmouth.omnibox_types import AddressAction, AddressAction_ChangeDirectory, AddressAction_Failed, AddressAction_Ignore, AddressAction_OpenExternally, AddressAction_Quit, AddressAction_ResolveForge, AddressAction_ShowAbout, AddressAction_ShowHelp, AddressAction_ShowPane, AddressAction_Visit, OmniboxCommand, OmniboxCommand_About, OmniboxCommand_Bookmarks, OmniboxCommand_ChangeDirectory, OmniboxCommand_Changelog, OmniboxCommand_Contents, OmniboxCommand_Discord, OmniboxCommand_Forge, OmniboxCommand_Help, OmniboxCommand_History, OmniboxCommand_Local, OmniboxCommand_Obsidian, OmniboxCommand_Quit
from frogmouth.document_types import BrowserFailure
from frogmouth.layout_types import Pane
from frogmouth.model_types import Forge, Location, LocationKind, LocationKind_Local, LocationKind_Remote

def parse_command(value: str) -> Option[OmniboxCommand]:
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
    value = _cott_validate_abi(value, str, path="$.value")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/omnibox/parse_command.py", "9eb5a1c076fe2a37a7500b86915150575f77c41e0cd70be115bbc9c01b7e0b7f", "parse_command", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.omnibox.parse_command")
        _result = _implementation(value)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.omnibox.parse_command"
        if _error.span is None:
            _error.span = {"end_byte":2154,"end_column":1,"end_line":61,"start_byte":832,"start_column":1,"start_line":37}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.omnibox.parse_command", phase="implementation-call", span={"end_byte":2154,"end_column":1,"end_line":61,"start_byte":832,"start_column":1,"start_line":37}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.omnibox.parse_command", phase="implementation-call", span={"end_byte":2154,"end_column":1,"end_line":61,"start_byte":832,"start_column":1,"start_line":37}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[OmniboxCommand], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and type(_cott_match_value.value) is OmniboxCommand_ChangeDirectory and True:
            target = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[0].name)
            return (_cott_contract_condition(((target in value)), "frogmouth.omnibox.parse_command", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.omnibox.parse_command", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.omnibox.parse_command", clause="ensures:1", phase="ensures", span={"end_byte":1964,"end_column":91,"end_line":55,"start_byte":1878,"start_column":5,"start_line":55}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and type(_cott_match_value.value) is OmniboxCommand_Obsidian and True:
            vault = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[0].name)
            return (_cott_contract_condition(((vault in value)), "frogmouth.omnibox.parse_command", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.omnibox.parse_command", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.omnibox.parse_command", clause="ensures:2", phase="ensures", span={"end_byte":2046,"end_column":82,"end_line":56,"start_byte":1969,"start_column":5,"start_line":56}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and type(_cott_match_value.value) is OmniboxCommand_Forge and True and True:
            arguments = getattr(_cott_match_value.value, _dataclasses.fields(type(_cott_match_value.value))[1].name)
            return (_cott_contract_condition(((arguments in value)), "frogmouth.omnibox.parse_command", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.omnibox.parse_command", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.omnibox.parse_command", clause="ensures:3", phase="ensures", span={"end_byte":2136,"end_column":90,"end_line":57,"start_byte":2051,"start_column":5,"start_line":57}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[OmniboxCommand], path="$.return", validator=_cott_validate_abi)
    return _result

def interpret_address(value: str, home: str, working_directory: str) -> AddressAction:
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
    value = _cott_validate_abi(value, str, path="$.value")
    home = _cott_validate_abi(home, str, path="$.home")
    working_directory = _cott_validate_abi(working_directory, str, path="$.working_directory")
    if not (_cott_contract_condition(((len(home) > 0)), "frogmouth.omnibox.interpret_address", "requires:1")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.omnibox.interpret_address", clause="requires:1", phase="requires", span={"end_byte":4250,"end_column":26,"end_line":95,"start_byte":4229,"start_column":5,"start_line":95}, expected="true", actual="false")
    if not (_cott_contract_condition(((len(working_directory) > 0)), "frogmouth.omnibox.interpret_address", "requires:2")):
        raise CottContractViolation("requires clause failed", symbol="frogmouth.omnibox.interpret_address", clause="requires:2", phase="requires", span={"end_byte":4289,"end_column":39,"end_line":96,"start_byte":4255,"start_column":5,"start_line":96}, expected="true", actual="false")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/omnibox/interpret_address.py", "81c5e9e4e2cfeffda6d04eab9f4bdc62afe49a9535f89b96ee3ec657bd83062f", "interpret_address", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.omnibox.interpret_address")
        _result = _implementation(value, home, working_directory)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.omnibox.interpret_address"
        if _error.span is None:
            _error.span = {"end_byte":4629,"end_column":1,"end_line":104,"start_byte":2154,"start_column":1,"start_line":61}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.omnibox.interpret_address", phase="implementation-call", span={"end_byte":4629,"end_column":1,"end_line":104,"start_byte":2154,"start_column":1,"start_line":61}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.omnibox.interpret_address", phase="implementation-call", span={"end_byte":4629,"end_column":1,"end_line":104,"start_byte":2154,"start_column":1,"start_line":61}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, AddressAction, path="$.return")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is AddressAction_Visit and True and True:
            location = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            address = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[1].name)
            return (_cott_contract_condition((((not ((location).kind == LocationKind_Local())) or (address == (location).target))), "frogmouth.omnibox.interpret_address", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.omnibox.interpret_address", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.omnibox.interpret_address", clause="ensures:3", phase="ensures", span={"end_byte":4414,"end_column":124,"end_line":98,"start_byte":4295,"start_column":5,"start_line":98}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is AddressAction_Visit and True and True:
            location = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            address = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[1].name)
            return (_cott_contract_condition((((not ((location).kind == LocationKind_Remote())) or (address == ""))), "frogmouth.omnibox.interpret_address", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.omnibox.interpret_address", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.omnibox.interpret_address", clause="ensures:4", phase="ensures", span={"end_byte":4526,"end_column":112,"end_line":99,"start_byte":4419,"start_column":5,"start_line":99}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is AddressAction_ResolveForge and True and True:
            candidates = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[1].name)
            return (_cott_contract_condition(((len(candidates) > 0)), "frogmouth.omnibox.interpret_address", "ensures:5"))
        _cott_contract_condition((False), "frogmouth.omnibox.interpret_address", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.omnibox.interpret_address", clause="ensures:5", phase="ensures", span={"end_byte":4602,"end_column":76,"end_line":100,"start_byte":4531,"start_column":5,"start_line":100}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, AddressAction, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["AddressAction", "AddressAction_ChangeDirectory", "AddressAction_Failed", "AddressAction_Ignore", "AddressAction_OpenExternally", "AddressAction_Quit", "AddressAction_ResolveForge", "AddressAction_ShowAbout", "AddressAction_ShowHelp", "AddressAction_ShowPane", "AddressAction_Visit", "OmniboxCommand", "OmniboxCommand_About", "OmniboxCommand_Bookmarks", "OmniboxCommand_ChangeDirectory", "OmniboxCommand_Changelog", "OmniboxCommand_Contents", "OmniboxCommand_Discord", "OmniboxCommand_Forge", "OmniboxCommand_Help", "OmniboxCommand_History", "OmniboxCommand_Local", "OmniboxCommand_Obsidian", "OmniboxCommand_Quit", "interpret_address", "parse_command"]
