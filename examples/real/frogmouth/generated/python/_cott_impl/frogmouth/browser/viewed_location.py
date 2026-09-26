from cott_runtime import Nothing, Option
from frogmouth.browser_types import BrowserState, ViewState_Viewing
from frogmouth.history import current_location
from frogmouth.model_types import Location


def viewed_location(session: BrowserState) -> Option[Location]:
    if isinstance(session.view, ViewState_Viewing):
        return current_location(session.history)
    return Nothing()
