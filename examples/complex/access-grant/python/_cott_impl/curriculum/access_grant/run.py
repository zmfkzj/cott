from cott_runtime import Ok
from curriculum.access_grant_types import Granted


def run() -> Ok[Granted]:
    return Ok(value=Granted())
