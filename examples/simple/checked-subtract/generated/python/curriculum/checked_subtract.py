from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.checked_subtract_types import CountError, Underflow

run = _cott_load("_cott_impl/curriculum/checked_subtract/run.py", "9453b332893e0222d4977ee6a26e027fe0d565a4cb597495d66f271a411bf3bf", "run")

__all__ = ["CountError", "Underflow", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
