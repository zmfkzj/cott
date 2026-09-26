from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.browser_types import BrowserState as BrowserState, NavigationEffect as NavigationEffect, NavigationEffect_ChangeDirectory as NavigationEffect_ChangeDirectory, NavigationEffect_Display as NavigationEffect_Display, NavigationEffect_Failed as NavigationEffect_Failed, NavigationEffect_Idle as NavigationEffect_Idle, NavigationEffect_OpenExternally as NavigationEffect_OpenExternally, NavigationEffect_Quit as NavigationEffect_Quit, NavigationEffect_ScrollToAnchor as NavigationEffect_ScrollToAnchor, NavigationEffect_ShowAbout as NavigationEffect_ShowAbout, NavigationEffect_ShowHelp as NavigationEffect_ShowHelp, NavigationEffect_ShowPane as NavigationEffect_ShowPane, NavigationRequest as NavigationRequest, NavigationRequest_Address as NavigationRequest_Address, NavigationRequest_Back as NavigationRequest_Back, NavigationRequest_Forward as NavigationRequest_Forward, NavigationRequest_HistoryEntry as NavigationRequest_HistoryEntry, NavigationRequest_Link as NavigationRequest_Link, NavigationRequest_Open as NavigationRequest_Open, NavigationRequest_Paste as NavigationRequest_Paste, NavigationRequest_Reload as NavigationRequest_Reload, NavigationRequest_Startup as NavigationRequest_Startup, NavigationResult as NavigationResult, ViewState as ViewState, ViewState_Placeholder as ViewState_Placeholder, ViewState_Viewing as ViewState_Viewing
from frogmouth.document_types import BrowserFailure
from frogmouth.history_types import History
from frogmouth.layout_types import Pane
from frogmouth.model_types import BrowserContext, Document, Location
"""The location being viewed: frogmouth.history.current_location of the
history while the view is Viewing, Nothing while the placeholder is
shown."""
def viewed_location(session: BrowserState) -> Option[Location]: ...

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
def navigate(session: BrowserState, request: NavigationRequest, context: BrowserContext) -> NavigationResult: ...

__all__ = ["BrowserState", "NavigationEffect", "NavigationEffect_ChangeDirectory", "NavigationEffect_Display", "NavigationEffect_Failed", "NavigationEffect_Idle", "NavigationEffect_OpenExternally", "NavigationEffect_Quit", "NavigationEffect_ScrollToAnchor", "NavigationEffect_ShowAbout", "NavigationEffect_ShowHelp", "NavigationEffect_ShowPane", "NavigationRequest", "NavigationRequest_Address", "NavigationRequest_Back", "NavigationRequest_Forward", "NavigationRequest_HistoryEntry", "NavigationRequest_Link", "NavigationRequest_Open", "NavigationRequest_Paste", "NavigationRequest_Reload", "NavigationRequest_Startup", "NavigationResult", "ViewState", "ViewState_Placeholder", "ViewState_Viewing", "navigate", "viewed_location"]
