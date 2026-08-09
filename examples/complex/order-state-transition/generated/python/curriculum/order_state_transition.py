from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.order_state_transition_types import OrderState, Pending, Paid, TransitionError, NotPending

run = _cott_load("_cott_impl/curriculum/order_state_transition/run.py", "df22436efcb1aef5c57c6a9861c5047b51f9538ea8fb46df798af778d6d859c9", "run")

__all__ = ["OrderState", "Pending", "Paid", "TransitionError", "NotPending", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
