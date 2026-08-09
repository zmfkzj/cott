from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.result_division_guard_types import DivideError, ZeroDivisor

run = _cott_load("_cott_impl/curriculum/result_division_guard/run.py", "76903f0e44de8c208ca74350aeec2987bcce3e45fcdaa3f88550648ec6096669", "run")

__all__ = ["DivideError", "ZeroDivisor", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
