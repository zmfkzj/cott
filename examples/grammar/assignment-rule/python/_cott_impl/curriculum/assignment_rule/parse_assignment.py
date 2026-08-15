from cott_runtime import Err, Ok, Result
from curriculum.assignment_rule_types import (
    Assignment,
    ParseAssignmentError,
    ParseAssignmentError_EmptyName,
)


def parse_assignment(line: str) -> Result[Assignment, ParseAssignmentError]:
    """Parse one assignment following strict assignment rules."""
    name, separator, value = line.partition("=")
    if not separator:
        return Err(error=ParseAssignmentError_EmptyName())

    name = name.strip()
    value = value.strip()
    if len(name) <= 1 or len(value) == 0:
        return Err(error=ParseAssignmentError_EmptyName())

    return Ok(value=Assignment(name=name, value=value))
