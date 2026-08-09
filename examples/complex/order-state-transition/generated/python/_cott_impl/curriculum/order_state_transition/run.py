from cott_runtime import Ok
from curriculum.order_state_transition_types import Paid


def run() -> Ok[Paid]:
    return Ok(value=Paid(receipt="r1"))
