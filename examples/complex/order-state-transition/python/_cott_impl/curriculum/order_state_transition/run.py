from cott_runtime import Ok, Result
from curriculum.order_state_transition_types import OrderState, OrderState_Paid, TransitionError


def run() -> Result[OrderState, TransitionError]:
    return Ok(value=OrderState_Paid(receipt="r1"))
