from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from frogmouth.document_types import BrowserFailure
from frogmouth.history_types import History
from frogmouth.layout_types import Pane
from frogmouth.model_types import BrowserContext, Document, Location

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewState_Placeholder:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ViewState_Viewing:
    pass

ViewState: TypeAlias = Union[ViewState_Placeholder, ViewState_Viewing]

"""The browser session: the browsing history and whether the viewer shows the
history's current location (Viewing) or the welcome placeholder."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BrowserState:
    __hash__ = None
    history: History
    view: ViewState

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "history", _cott_validate_abi(self.history, History, path="$.history"))
        if not _cott_validated_construction():
            object.__setattr__(self, "view", _cott_validate_abi(self.view, ViewState, path="$.view"))

"""One user navigation. Startup carries the command-line location; Address is
submitted address-bar text; Link is a clicked, percent-decoded link target;
Paste is pasted text; Open is a location chosen in the local file browser or
the bookmarks; HistoryEntry is the index of a location chosen in the history
pane."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationRequest_Startup:
    __hash__ = None
    address: Option[str]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationRequest_Address:
    __hash__ = None
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationRequest_Link:
    __hash__ = None
    href: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationRequest_Paste:
    __hash__ = None
    text: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationRequest_Open:
    __hash__ = None
    location: Location

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationRequest_HistoryEntry:
    __hash__ = None
    history_id: U64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationRequest_Back:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationRequest_Forward:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationRequest_Reload:
    pass

NavigationRequest: TypeAlias = Union[NavigationRequest_Startup, NavigationRequest_Address, NavigationRequest_Link, NavigationRequest_Paste, NavigationRequest_Open, NavigationRequest_HistoryEntry, NavigationRequest_Back, NavigationRequest_Forward, NavigationRequest_Reload]

"""What the screen must do after a navigation. Display shows a loaded document
from its top, then scrolls to the heading anchor if one is given;
ChangeDirectory shows the local file browser rooted at path; ShowPane toggles
that sidebar pane; Idle does nothing."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationEffect_Display:
    __hash__ = None
    document: Document
    anchor: Option[str]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationEffect_ScrollToAnchor:
    __hash__ = None
    anchor: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationEffect_OpenExternally:
    __hash__ = None
    target: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationEffect_ChangeDirectory:
    __hash__ = None
    path: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationEffect_ShowPane:
    __hash__ = None
    pane: Pane

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationEffect_ShowHelp:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationEffect_ShowAbout:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationEffect_Quit:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationEffect_Failed:
    __hash__ = None
    failure: BrowserFailure

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationEffect_Idle:
    pass

NavigationEffect: TypeAlias = Union[NavigationEffect_Display, NavigationEffect_ScrollToAnchor, NavigationEffect_OpenExternally, NavigationEffect_ChangeDirectory, NavigationEffect_ShowPane, NavigationEffect_ShowHelp, NavigationEffect_ShowAbout, NavigationEffect_Quit, NavigationEffect_Failed, NavigationEffect_Idle]

"""The outcome of a navigation: the new session state, the screen effect, and
the text the address bar must show (Nothing leaves it unchanged)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class NavigationResult:
    __hash__ = None
    session: BrowserState
    effect: NavigationEffect
    address: Option[str]

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "session", _cott_validate_abi(self.session, BrowserState, path="$.session"))
        if not _cott_validated_construction():
            object.__setattr__(self, "effect", _cott_validate_abi(self.effect, NavigationEffect, path="$.effect"))
        if not _cott_validated_construction():
            object.__setattr__(self, "address", _cott_validate_abi(self.address, Option[str], path="$.address"))

"""The location being viewed: frogmouth.history.current_location of the
history while the view is Viewing, Nothing while the placeholder is
shown."""
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
__all__ = ["BrowserState", "NavigationEffect", "NavigationEffect_ChangeDirectory", "NavigationEffect_Display", "NavigationEffect_Failed", "NavigationEffect_Idle", "NavigationEffect_OpenExternally", "NavigationEffect_Quit", "NavigationEffect_ScrollToAnchor", "NavigationEffect_ShowAbout", "NavigationEffect_ShowHelp", "NavigationEffect_ShowPane", "NavigationRequest", "NavigationRequest_Address", "NavigationRequest_Back", "NavigationRequest_Forward", "NavigationRequest_HistoryEntry", "NavigationRequest_Link", "NavigationRequest_Open", "NavigationRequest_Paste", "NavigationRequest_Reload", "NavigationRequest_Startup", "NavigationResult", "ViewState", "ViewState_Placeholder", "ViewState_Viewing"]
