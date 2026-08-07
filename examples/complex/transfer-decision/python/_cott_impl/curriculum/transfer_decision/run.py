from cott_runtime import Ok
from curriculum.transfer_decision_types import Accepted


def run() -> Ok[Accepted]:
    return Ok(value=Accepted())
