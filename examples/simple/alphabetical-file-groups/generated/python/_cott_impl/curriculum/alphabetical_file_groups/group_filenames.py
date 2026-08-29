from cott_runtime import CottList, Err, Ok, Result
from curriculum.alphabetical_file_groups import classify_filename
from curriculum.alphabetical_file_groups_types import FileGroupError, FileMove


def group_filenames(filenames: CottList[str]) -> Result[CottList[FileMove], FileGroupError]:
    moves: list[FileMove] = []
    for filename in filenames:
        result = classify_filename(filename)
        match result:
            case Ok(value=move):
                moves.append(move)
            case Err():
                return result
    return Ok(value=CottList(values=moves))
