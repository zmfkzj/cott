from rich.markup import escape

from frogmouth.document_types import BrowserFailure, BrowserFailure_DoesNotExist, BrowserFailure_ForgeUnresolved, BrowserFailure_NoSuchDirectory, BrowserFailure_NotADirectory, BrowserFailure_NotBookmarkable, BrowserFailure_UnhandledLink, LoadError_LocalFailed
from frogmouth.model_types import Dialog, Forge, Forge_BitBucket, Forge_Codeberg, Forge_GitHub, Forge_GitLab


def _is_forge(forge: Forge, candidate: object) -> bool:
    if forge is candidate or forge == candidate:
        return True
    return isinstance(candidate, type) and isinstance(forge, candidate)


def _forge_name(forge: Forge) -> str:
    if _is_forge(forge, Forge_GitHub):
        return "GitHub"
    if _is_forge(forge, Forge_GitLab):
        return "GitLab"
    if _is_forge(forge, Forge_BitBucket):
        return "BitBucket"
    if _is_forge(forge, Forge_Codeberg):
        return "Codeberg"
    raise ValueError(f"unknown forge: {forge!r}")


def failure_dialog(failure: BrowserFailure) -> Dialog:
    if isinstance(failure, BrowserFailure_DoesNotExist):
        return Dialog(title="Does not exist", message=f"Unable to open {escape(failure.path)} because it does not exist.")
    if isinstance(failure, BrowserFailure_NoSuchDirectory):
        return Dialog(title="No such directory", message=f"{escape(failure.path)} does not exist.")
    if isinstance(failure, BrowserFailure_NotADirectory):
        return Dialog(title="Not a directory", message=f"{escape(failure.path)} is not a directory.")
    if isinstance(failure, BrowserFailure_ForgeUnresolved):
        name = escape(_forge_name(failure.forge))
        return Dialog(
            title=f"Unable to work out a {name} URL",
            message=f"After trying a few options it hasn't been possible to work out the {name} URL.\n\nPerhaps the file you're after is on an unusual branch, or the spelling is wrong?",
        )
    if isinstance(failure, BrowserFailure_UnhandledLink):
        return Dialog(title="Unable to handle link", message=f"Unable to work out how to handle this link:\n\n{escape(failure.href)}")
    if isinstance(failure, BrowserFailure_NotBookmarkable):
        return Dialog(title="Not a bookmarkable location", message="The current view can't be bookmarked.")
    cause = failure.cause
    if isinstance(cause, LoadError_LocalFailed):
        return Dialog(title="Error loading local document", message=f"{escape(cause.path)}\n\n{escape(cause.message)}.")
    return Dialog(title="Error getting document", message=escape(cause.message))
