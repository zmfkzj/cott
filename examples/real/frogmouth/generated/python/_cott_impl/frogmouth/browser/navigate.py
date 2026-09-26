from cott_runtime import Nothing, Ok, Option, Some
from frogmouth.browser import viewed_location
from frogmouth.document import resolve_link, visit_location
from frogmouth.forge import locate_forge_file
from frogmouth.history import current_location, remember_location, step_back, step_forward
from frogmouth.locations import inspect_local_path, normalize_local_path
from frogmouth.omnibox import interpret_address
from frogmouth.browser_types import BrowserState, NavigationEffect, NavigationEffect_ChangeDirectory, NavigationEffect_Display, NavigationEffect_Failed, NavigationEffect_Idle, NavigationEffect_OpenExternally, NavigationEffect_Quit, NavigationEffect_ScrollToAnchor, NavigationEffect_ShowAbout, NavigationEffect_ShowHelp, NavigationEffect_ShowPane, NavigationRequest, NavigationRequest_Address, NavigationRequest_Back, NavigationRequest_HistoryEntry, NavigationRequest_Forward, NavigationRequest_Link, NavigationRequest_Open, NavigationRequest_Paste, NavigationRequest_Reload, NavigationRequest_Startup, NavigationResult, ViewState_Viewing
from frogmouth.document_types import BrowserFailure_ForgeUnresolved, LinkAction_Anchor, LinkAction_Failed, LinkAction_OpenExternally, LinkAction_Visit, VisitOutcome_Failed, VisitOutcome_Loaded, VisitOutcome_OpenExternally
from frogmouth.model_types import BrowserContext, Location, LocationKind_Local, PathKind_Missing
from frogmouth.omnibox_types import AddressAction_ChangeDirectory, AddressAction_Failed, AddressAction_OpenExternally, AddressAction_Quit, AddressAction_ResolveForge, AddressAction_ShowAbout, AddressAction_ShowHelp, AddressAction_ShowPane, AddressAction_Visit


def _idle(session: BrowserState) -> NavigationResult:
    return NavigationResult(session=session, effect=NavigationEffect_Idle(), address=Nothing())


def _visit(session: BrowserState, location: Location, anchor: Option[str], remember: bool, context: BrowserContext) -> NavigationResult:
    outcome = visit_location(location, context)
    if isinstance(outcome, VisitOutcome_Loaded):
        document = outcome.document
        history = remember_location(session.history, document.location) if remember else session.history
        return NavigationResult(session=BrowserState(history=history, view=ViewState_Viewing()), effect=NavigationEffect_Display(document=document, anchor=anchor), address=Some(value=document.location.target))
    effect: NavigationEffect
    if isinstance(outcome, VisitOutcome_OpenExternally):
        effect = NavigationEffect_OpenExternally(target=outcome.target)
    else:
        assert isinstance(outcome, VisitOutcome_Failed)
        effect = NavigationEffect_Failed(failure=outcome.failure)
    return NavigationResult(session=session, effect=effect, address=Nothing())


def _with_address(result: NavigationResult, address: str) -> NavigationResult:
    if isinstance(result.effect, NavigationEffect_Display):
        return result
    return NavigationResult(session=result.session, effect=result.effect, address=Some(value=address))


def _address(session: BrowserState, value: str, context: BrowserContext) -> NavigationResult:
    action = interpret_address(value, context.home, context.working_directory)
    if isinstance(action, AddressAction_Visit):
        return _with_address(_visit(session, action.location, Nothing(), True, context), action.address)
    if isinstance(action, AddressAction_ResolveForge):
        found = locate_forge_file(action.forge, action.candidates)
        if isinstance(found, Ok):
            return _with_address(_visit(session, found.value, Nothing(), True, context), "")
        return NavigationResult(session=session, effect=NavigationEffect_Failed(failure=BrowserFailure_ForgeUnresolved(forge=found.error.forge)), address=Some(value=""))
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
        effect = NavigationEffect_Idle()
    return NavigationResult(session=session, effect=effect, address=Some(value=""))


def navigate(session: BrowserState, request: NavigationRequest, context: BrowserContext) -> NavigationResult:
    if isinstance(request, NavigationRequest_Address):
        return _address(session, request.value, context)
    if isinstance(request, NavigationRequest_Startup):
        if isinstance(request.address, Some):
            return _address(session, request.address.value, context)
        locations = session.history.locations
        if len(locations) == 0:
            return _idle(session)
        newest = locations[len(locations) - 1]
        result = _visit(session, newest, Nothing(), False, context)
        return NavigationResult(session=result.session, effect=result.effect, address=Some(value=newest.target))
    if isinstance(request, NavigationRequest_Link):
        link = resolve_link(request.href, viewed_location(session), context)
        if isinstance(link, LinkAction_Visit):
            return _visit(session, link.location, link.anchor, True, context)
        if isinstance(link, LinkAction_Anchor):
            return NavigationResult(session=session, effect=NavigationEffect_ScrollToAnchor(anchor=link.anchor), address=Nothing())
        if isinstance(link, LinkAction_OpenExternally):
            return NavigationResult(session=session, effect=NavigationEffect_OpenExternally(target=link.target), address=Nothing())
        assert isinstance(link, LinkAction_Failed)
        return NavigationResult(session=session, effect=NavigationEffect_Failed(failure=link.failure), address=Nothing())
    if isinstance(request, NavigationRequest_Paste):
        text = request.text
        if text == "":
            return _idle(session)
        path = normalize_local_path(context.working_directory, text)
        if isinstance(inspect_local_path(path), PathKind_Missing):
            return _idle(session)
        return _visit(session, Location(kind=LocationKind_Local(), target=path), Nothing(), True, context)
    if isinstance(request, NavigationRequest_Open):
        return _visit(session, request.location, Nothing(), True, context)
    if isinstance(request, NavigationRequest_HistoryEntry):
        locations = session.history.locations
        index = request.history_id
        if index >= len(locations):
            return _idle(session)
        chosen = locations[index]
        viewed = viewed_location(session)
        remember = not (isinstance(viewed, Some) and viewed.value == chosen)
        return _visit(session, chosen, Nothing(), remember, context)
    if isinstance(request, NavigationRequest_Back) or isinstance(request, NavigationRequest_Forward):
        moved = step_back(session.history) if isinstance(request, NavigationRequest_Back) else step_forward(session.history)
        if not isinstance(moved, Some):
            return _idle(session)
        target = current_location(moved.value)
        if not isinstance(target, Some):
            return _idle(session)
        moved_session = BrowserState(history=moved.value, view=session.view)
        return _visit(moved_session, target.value, Nothing(), False, context)
    assert isinstance(request, NavigationRequest_Reload)
    viewed = viewed_location(session)
    if not isinstance(viewed, Some):
        return _idle(session)
    return _visit(session, viewed.value, Nothing(), False, context)
