from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.constant_greeting_types import GREETING

run = _cott_load("_cott_impl/curriculum/constant_greeting/run.py", "d1023d035a86e5654d983d78abe71fa4b13912ccbfa2cd1f98cc67fcd1d19daa", "run")

__all__ = ["GREETING", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
