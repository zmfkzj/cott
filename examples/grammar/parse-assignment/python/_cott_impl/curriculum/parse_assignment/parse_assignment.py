from cott_runtime import Err, Ok, Result
from curriculum.parse_assignment_types import (
    Assignment,
    ParseAssignmentError,
    ParseAssignmentError_EmptyName,
    ParseAssignmentError_MissingEquals,
)


def parse_assignment(line: str) -> Result[Assignment, ParseAssignmentError]:
    """Parse one trimmed name=value assignment."""
    name, separator, value = line.partition("=")
    if not separator:
        return Err(error=ParseAssignmentError_MissingEquals())

    name = name.strip()
    if not name:
        return Err(error=ParseAssignmentError_EmptyName())

    return Ok(value=Assignment(name=name, value=value.strip()))
