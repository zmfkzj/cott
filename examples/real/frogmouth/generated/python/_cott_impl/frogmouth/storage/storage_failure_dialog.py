from rich.markup import escape

from frogmouth.model_types import Dialog
from frogmouth.storage_types import StoreError, StoreError_WriteFailed


def storage_failure_dialog(failure: StoreError) -> Dialog:
    if isinstance(failure, StoreError_WriteFailed):
        title = "Unable to save application data"
    else:
        title = "Unable to load application data"
    return Dialog(title=title, message=f"{escape(failure.path)}\n\n{escape(failure.message)}.")
