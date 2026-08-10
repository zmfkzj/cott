from cott_runtime import CottList, Err, Ok, Result
from curriculum.alphabetical_file_groups import classify_filename
from curriculum.alphabetical_file_groups_types import FileGroupError, FileMove


def group_filenames(filenames: CottList[str]) -> Result[CottList[FileMove], FileGroupError]:
    moves: list[FileMove] = []
    for filename in filenames:
        result = classify_filename(filename)
        if isinstance(result, Err):
            return Err(error=result.error)
        moves.append(result.value)
    return Ok(value=CottList(values=moves))
