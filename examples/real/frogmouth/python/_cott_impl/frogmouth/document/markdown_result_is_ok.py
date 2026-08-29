from cott_runtime import Err, Ok, Result
from frogmouth.document_types import LoadError


def markdown_result_is_ok(value: Result[str, LoadError]) -> bool:
    match value:
        case Ok():
            return True
        case Err():
            return False
