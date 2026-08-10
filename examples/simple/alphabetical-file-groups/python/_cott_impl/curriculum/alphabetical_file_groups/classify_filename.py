from cott_runtime import Err, Ok, Result
from curriculum.alphabetical_file_groups_types import FileGroupError, FileGroupError_EmptyFilename, FileMove


def classify_filename(filename: str) -> Result[FileMove, FileGroupError]:
    if filename == "":
        return Err(error=FileGroupError_EmptyFilename())
    leading = filename[0]
    folder = leading.casefold() if leading.isalpha() else "misc"
    return Ok(value=FileMove(filename=filename, folder=folder))
