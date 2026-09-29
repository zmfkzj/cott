from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from frogmouth.browser_types import BrowserState, NavigationEffect, NavigationEffect_ChangeDirectory, NavigationEffect_Display, NavigationEffect_Failed, NavigationEffect_Idle, NavigationEffect_OpenExternally, NavigationEffect_Quit, NavigationEffect_ScrollToAnchor, NavigationEffect_ShowAbout, NavigationEffect_ShowHelp, NavigationEffect_ShowPane, NavigationRequest, NavigationRequest_Address, NavigationRequest_Back, NavigationRequest_Forward, NavigationRequest_HistoryEntry, NavigationRequest_Link, NavigationRequest_Open, NavigationRequest_Paste, NavigationRequest_Reload, NavigationRequest_Startup, NavigationResult, ViewState, ViewState_Placeholder, ViewState_Viewing
from frogmouth.document_types import BrowserFailure
from frogmouth.history_types import History
from frogmouth.layout_types import Pane
from frogmouth.model_types import BrowserContext, Document, Location

def viewed_location(session: BrowserState) -> Option[Location]:
    """The location being viewed: frogmouth.history.current_location of the
history while the view is Viewing, Nothing while the placeholder is
shown."""
    session = _cott_validate_abi(session, BrowserState, path="$.session")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/browser/viewed_location.py", "8178ac0497baac0eb50daaea05d085d877e93d46c2b144784f5ad3350a01e3a0", "viewed_location", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.browser.viewed_location")
        _result = _implementation(session)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.browser.viewed_location"
        if _error.span is None:
            _error.span = {"end_byte":2203,"end_column":1,"end_line":77,"start_byte":1818,"start_column":1,"start_line":65}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.browser.viewed_location", phase="implementation-call", span={"end_byte":2203,"end_column":1,"end_line":77,"start_byte":1818,"start_column":1,"start_line":65}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.browser.viewed_location", phase="implementation-call", span={"end_byte":2203,"end_column":1,"end_line":77,"start_byte":1818,"start_column":1,"start_line":65}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Option[Location], path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            return (_cott_contract_condition((((session).view == ViewState_Viewing())), "frogmouth.browser.viewed_location", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.browser.viewed_location", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.browser.viewed_location", clause="ensures:1", phase="ensures", span={"end_byte":2121,"end_column":64,"end_line":72,"start_byte":2062,"start_column":5,"start_line":72}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Some and True:
            return (_cott_contract_condition(((len(((session).history).locations) > 0)), "frogmouth.browser.viewed_location", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.browser.viewed_location", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.browser.viewed_location", clause="ensures:2", phase="ensures", span={"end_byte":2185,"end_column":64,"end_line":73,"start_byte":2126,"start_column":5,"start_line":73}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Option[Location], path="$.return", validator=_cott_validate_abi)
    return _result

def navigate(session: BrowserState, request: NavigationRequest, context: BrowserContext) -> NavigationResult:
    """The browser's navigation root: one request becomes the new session, one
screen effect and the address-bar text.

VISIT(location, anchor, remember) calls
frogmouth.document.visit_location(location, context). Loaded(document)
is Display(document, anchor) with the view Viewing, the history
frogmouth.history.remember_location(history, document.location) when
remember holds (unchanged otherwise), and the address
document.location.target. OpenExternally(target) and Failed(failure)
become the effects of the same name and keep the session the visit started
from.

Address(value): frogmouth.omnibox.interpret_address(value, context.home,
context.working_directory) decides. Visit(location, address) is
VISIT(location, Nothing, remember). ResolveForge(forge, candidates)
calls frogmouth.forge.locate_forge_file(forge, candidates) and VISITs
the found location with remember; its error Unresolved(forge) is
Failed(ForgeUnresolved(forge)).
ChangeDirectory, OpenExternally, ShowPane, ShowHelp, ShowAbout, Quit and
Failed become the effect of the same name; Ignore is Idle. Unless a
document was displayed, the address is the Visit's address, or "" for
every other action.

Startup(address): a present address is handled exactly as
Address(address). Without one, a non-empty history VISITs its newest
location with Nothing and without remember, and the address is that
location's target whatever the outcome; an empty history is Idle.

Link(href): frogmouth.document.resolve_link(href,
frogmouth.browser.viewed_location(session), context) decides.
Visit(location, anchor) is VISIT(location, anchor, remember);
Anchor(anchor) is ScrollToAnchor(anchor); OpenExternally and Failed are
the effects of the same name.

Paste(text): for non-empty text whose path
frogmouth.locations.normalize_local_path(context.working_directory,
text) is not Missing according to
frogmouth.locations.inspect_local_path, VISIT the Local location of that
path with Nothing and remember; any other text is Idle.

Open(location) is VISIT(location, Nothing, remember).

HistoryEntry(history_id): the history location at that index is VISITed
with Nothing, remembering it exactly when it differs from
viewed_location(session); an index outside the history is Idle.

Back and Forward: frogmouth.history.step_back or step_forward. Nothing
is Idle. Otherwise the moved history replaces the session's history even
when the visit fails, and its current location is VISITed with Nothing
and without remember.

Reload: viewed_location(session) is VISITed with Nothing and without
remember; without a viewed location it is Idle.

Except where stated above, the address is Nothing, and Idle keeps session."""
    session = _cott_validate_abi(session, BrowserState, path="$.session")
    request = _cott_validate_abi(request, NavigationRequest, path="$.request")
    context = _cott_validate_abi(context, BrowserContext, path="$.context")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/browser/navigate.py", "20374f880c0fed5dec7ddb617cdaf23cdedfbb1f35435b8a454ad60d941ddfcc", "navigate", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.browser.navigate")
        _result = _implementation(session, request, context)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.browser.navigate"
        if _error.span is None:
            _error.span = {"end_byte":5965,"end_column":1,"end_line":149,"start_byte":2203,"start_column":1,"start_line":77}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.browser.navigate", phase="implementation-call", span={"end_byte":5965,"end_column":1,"end_line":149,"start_byte":2203,"start_column":1,"start_line":77}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.browser.navigate", phase="implementation-call", span={"end_byte":5965,"end_column":1,"end_line":149,"start_byte":2203,"start_column":1,"start_line":77}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, NavigationResult, path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = (_result).effect
        if type(_cott_match_value) is NavigationEffect_Display and True and True:
            return (_cott_contract_condition(((((_result).session).view == ViewState_Viewing())), "frogmouth.browser.navigate", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.browser.navigate", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.browser.navigate", clause="ensures:1", phase="ensures", span={"end_byte":5339,"end_column":111,"end_line":140,"start_byte":5233,"start_column":5,"start_line":140}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = (_result).effect
        if type(_cott_match_value) is NavigationEffect_Idle:
            return (_cott_contract_condition((((_result).session == session)), "frogmouth.browser.navigate", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.browser.navigate", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.browser.navigate", clause="ensures:2", phase="ensures", span={"end_byte":5424,"end_column":85,"end_line":141,"start_byte":5344,"start_column":5,"start_line":141}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = (_result).effect
        if type(_cott_match_value) is NavigationEffect_ScrollToAnchor and True:
            return (_cott_contract_condition((((_result).session == session)), "frogmouth.browser.navigate", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.browser.navigate", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.browser.navigate", clause="ensures:3", phase="ensures", span={"end_byte":5522,"end_column":98,"end_line":142,"start_byte":5429,"start_column":5,"start_line":142}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = (_result).effect
        if type(_cott_match_value) is NavigationEffect_Failed and True:
            return (_cott_contract_condition(((((_result).session).view == (session).view)), "frogmouth.browser.navigate", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.browser.navigate", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.browser.navigate", clause="ensures:4", phase="ensures", span={"end_byte":5622,"end_column":100,"end_line":143,"start_byte":5527,"start_column":5,"start_line":143}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = request
        if type(_cott_match_value) is NavigationRequest_Reload:
            return (_cott_contract_condition(((((_result).session).history == (session).history)), "frogmouth.browser.navigate", "ensures:5"))
        _cott_contract_condition((False), "frogmouth.browser.navigate", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.browser.navigate", clause="ensures:5", phase="ensures", span={"end_byte":5720,"end_column":98,"end_line":144,"start_byte":5627,"start_column":5,"start_line":144}, expected="true", actual="false")
    def _cott_match_ensures_6() -> bool:
        _cott_match_value = request
        if type(_cott_match_value) is NavigationRequest_Link and True:
            return (_cott_contract_condition((((len((((_result).session).history).locations) == len(((session).history).locations)) or (((((_result).session).history).current + 1) == len((((_result).session).history).locations)))), "frogmouth.browser.navigate", "ensures:6"))
        _cott_contract_condition((False), "frogmouth.browser.navigate", "ensures:6:applicable")
        return True
    if not (_cott_match_ensures_6()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.browser.navigate", clause="ensures:6", phase="ensures", span={"end_byte":5929,"end_column":209,"end_line":145,"start_byte":5725,"start_column":5,"start_line":145}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, NavigationResult, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["BrowserState", "NavigationEffect", "NavigationEffect_ChangeDirectory", "NavigationEffect_Display", "NavigationEffect_Failed", "NavigationEffect_Idle", "NavigationEffect_OpenExternally", "NavigationEffect_Quit", "NavigationEffect_ScrollToAnchor", "NavigationEffect_ShowAbout", "NavigationEffect_ShowHelp", "NavigationEffect_ShowPane", "NavigationRequest", "NavigationRequest_Address", "NavigationRequest_Back", "NavigationRequest_Forward", "NavigationRequest_HistoryEntry", "NavigationRequest_Link", "NavigationRequest_Open", "NavigationRequest_Paste", "NavigationRequest_Reload", "NavigationRequest_Startup", "NavigationResult", "ViewState", "ViewState_Placeholder", "ViewState_Viewing", "navigate", "viewed_location"]
