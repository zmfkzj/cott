from cott_runtime import Err, Result
from real.pgcli_types import ClientError, ClientError_EditorFailed, EditorRequest, InputBuffer


def edit_in_editor(request: EditorRequest) -> Result[InputBuffer, ClientError]:
    return Err(
        error=ClientError_EditorFailed(
            message="external editor requires an unavailable file host binding",
        )
    )
