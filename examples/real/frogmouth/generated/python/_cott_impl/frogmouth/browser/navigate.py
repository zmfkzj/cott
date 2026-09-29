from cott_runtime import Nothing, Ok, Option, Some, U64
from frogmouth.browser import viewed_location
from frogmouth.document import resolve_link, visit_location
from frogmouth.forge import locate_forge_file
from frogmouth.history import current_location, remember_location, step_back, step_forward
from frogmouth.locations import inspect_local_path, normalize_local_path
from frogmouth.omnibox import interpret_address
from frogmouth.browser_types import BrowserState, NavigationEffect, NavigationEffect_ChangeDirectory, NavigationEffect_Display, NavigationEffect_Failed, NavigationEffect_Idle, NavigationEffect_OpenExternally, NavigationEffect_Quit, NavigationEffect_ScrollToAnchor, NavigationEffect_ShowAbout, NavigationEffect_ShowHelp, NavigationEffect_ShowPane, NavigationRequest, NavigationRequest_Address, NavigationRequest_Back, NavigationRequest_Forward, NavigationRequest_HistoryEntry, NavigationRequest_Link, NavigationRequest_Open, NavigationRequest_Paste, NavigationRequest_Startup, NavigationResult, ViewState_Viewing
from frogmouth.document_types import BrowserFailure_ForgeUnresolved, LinkAction_Anchor, LinkAction_OpenExternally, LinkAction_Visit, VisitOutcome_Loaded, VisitOutcome_OpenExternally
from frogmouth.history_types import History
from frogmouth.model_types import BrowserContext, Location, LocationKind_Local, PathKind_Missing
from frogmouth.omnibox_types import AddressAction_ChangeDirectory, AddressAction_Failed, AddressAction_OpenExternally, AddressAction_Quit, AddressAction_ResolveForge, AddressAction_ShowAbout, AddressAction_ShowHelp, AddressAction_ShowPane, AddressAction_Visit


def _idle(session: BrowserState) -> NavigationResult:
    return NavigationResult(session=session, effect=NavigationEffect_Idle(), address=Nothing())


def _effect_only(session: BrowserState, effect: NavigationEffect) -> NavigationResult:
    return NavigationResult(session=session, effect=effect, address=Nothing())


def _with_address(result: NavigationResult, address: str) -> NavigationResult:
    return NavigationResult(session=result.session, effect=result.effect, address=Some(value=address))


def _unless_displayed(result: NavigationResult, address: str) -> NavigationResult:
    # A displayed document keeps the address VISIT gave it; every other outcome shows `address`.
    if isinstance(result.effect, NavigationEffect_Display):
        return result
    return _with_address(result, address)


def _visit(session: BrowserState, location: Location, anchor: Option[str], remember: bool, context: BrowserContext) -> NavigationResult:
    outcome = visit_location(location, context)
    if isinstance(outcome, VisitOutcome_Loaded):
        document = outcome.document
        history = remember_location(session.history, document.location) if remember else session.history
        shown = BrowserState(history=history, view=ViewState_Viewing())
        return NavigationResult(session=shown, effect=NavigationEffect_Display(document=document, anchor=anchor), address=Some(value=document.location.target))
    if isinstance(outcome, VisitOutcome_OpenExternally):
        return _effect_only(session, NavigationEffect_OpenExternally(target=outcome.target))
    return _effect_only(session, NavigationEffect_Failed(failure=outcome.failure))


def _submit_address(session: BrowserState, value: str, context: BrowserContext) -> NavigationResult:
    action = interpret_address(value, context.home, context.working_directory)
    if isinstance(action, AddressAction_Visit):
        return _unless_displayed(_visit(session, action.location, Nothing(), True, context), action.address)
    if isinstance(action, AddressAction_ResolveForge):
        found = locate_forge_file(action.forge, action.candidates)
        if isinstance(found, Ok):
            return _unless_displayed(_visit(session, found.value, Nothing(), True, context), "")
        return _with_address(_effect_only(session, NavigationEffect_Failed(failure=BrowserFailure_ForgeUnresolved(forge=found.error.forge))), "")
    effect: NavigationEffect
    if isinstance(action, AddressAction_ChangeDirectory):
        effect = NavigationEffect_ChangeDirectory(path=action.path)
    elif isinstance(action, AddressAction_OpenExternally):
        effect = NavigationEffect_OpenExternally(target=action.target)
    elif isinstance(action, AddressAction_ShowPane):
        effect = NavigationEffect_ShowPane(pane=action.pane)
    elif isinstance(action, AddressAction_ShowHelp):
        effect = NavigationEffect_ShowHelp()
    elif isinstance(action, AddressAction_ShowAbout):
        effect = NavigationEffect_ShowAbout()
    elif isinstance(action, AddressAction_Quit):
        effect = NavigationEffect_Quit()
    elif isinstance(action, AddressAction_Failed):
        effect = NavigationEffect_Failed(failure=action.failure)
    else:
        # Ignore
        effect = NavigationEffect_Idle()
    return _with_address(_effect_only(session, effect), "")


def _revisit_newest(session: BrowserState, context: BrowserContext) -> NavigationResult:
    locations = session.history.locations
    if len(locations) == 0:
        return _idle(session)
    newest = locations[len(locations) - 1]
    # The address is the newest location's target whatever the outcome, not the loaded document's.
    return _with_address(_visit(session, newest, Nothing(), False, context), newest.target)


def _follow_link(session: BrowserState, href: str, context: BrowserContext) -> NavigationResult:
    action = resolve_link(href, viewed_location(session), context)
    if isinstance(action, LinkAction_Visit):
        return _visit(session, action.location, action.anchor, True, context)
    if isinstance(action, LinkAction_Anchor):
        return _effect_only(session, NavigationEffect_ScrollToAnchor(anchor=action.anchor))
    if isinstance(action, LinkAction_OpenExternally):
        return _effect_only(session, NavigationEffect_OpenExternally(target=action.target))
    return _effect_only(session, NavigationEffect_Failed(failure=action.failure))


def _paste(session: BrowserState, text: str, context: BrowserContext) -> NavigationResult:
    if text == "":
        return _idle(session)
    path = normalize_local_path(context.working_directory, text)
    if isinstance(inspect_local_path(path), PathKind_Missing):
        return _idle(session)
    return _visit(session, Location(kind=LocationKind_Local(), target=path), Nothing(), True, context)


def _choose_history_entry(session: BrowserState, history_id: U64, context: BrowserContext) -> NavigationResult:
    locations = session.history.locations
    if history_id >= len(locations):
        return _idle(session)
    chosen = locations[history_id]
    viewed = viewed_location(session)
    already_viewed = isinstance(viewed, Some) and viewed.value == chosen
    return _visit(session, chosen, Nothing(), not already_viewed, context)


def _move(session: BrowserState, moved: Option[History], context: BrowserContext) -> NavigationResult:
    if not isinstance(moved, Some):
        return _idle(session)
    target = current_location(moved.value)
    assert isinstance(target, Some), "a moved history is never empty"
    # The moved history replaces the session's history even when the visit fails.
    return _visit(BrowserState(history=moved.value, view=session.view), target.value, Nothing(), False, context)


def _reload(session: BrowserState, context: BrowserContext) -> NavigationResult:
    viewed = viewed_location(session)
    if isinstance(viewed, Some):
        return _visit(session, viewed.value, Nothing(), False, context)
    return _idle(session)


def navigate(session: BrowserState, request: NavigationRequest, context: BrowserContext) -> NavigationResult:
    if isinstance(request, NavigationRequest_Address):
        return _submit_address(session, request.value, context)
    if isinstance(request, NavigationRequest_Startup):
        if isinstance(request.address, Some):
            return _submit_address(session, request.address.value, context)
        return _revisit_newest(session, context)
    if isinstance(request, NavigationRequest_Link):
        return _follow_link(session, request.href, context)
    if isinstance(request, NavigationRequest_Paste):
        return _paste(session, request.text, context)
    if isinstance(request, NavigationRequest_Open):
        return _visit(session, request.location, Nothing(), True, context)
    if isinstance(request, NavigationRequest_HistoryEntry):
        return _choose_history_entry(session, request.history_id, context)
    if isinstance(request, NavigationRequest_Back):
        return _move(session, step_back(session.history), context)
    if isinstance(request, NavigationRequest_Forward):
        return _move(session, step_forward(session.history), context)
    # Reload
    return _reload(session, context)
