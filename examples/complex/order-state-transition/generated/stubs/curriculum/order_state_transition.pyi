from __future__ import annotations

from typing import TypeAlias, Union

from curriculum.order_state_transition_types import OrderState, Pending, Paid, TransitionError, NotPending
OrderState: TypeAlias = Union[Pending, Paid]

TransitionError: TypeAlias = Union[NotPending]

def run() -> Result[OrderState, TransitionError]: ...
