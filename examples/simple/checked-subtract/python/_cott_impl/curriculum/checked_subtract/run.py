from cott_runtime import Ok, Result, U64
from curriculum.checked_subtract_types import CountError


def run() -> Result[U64, CountError]:
    return Ok(value=9 - 4)
