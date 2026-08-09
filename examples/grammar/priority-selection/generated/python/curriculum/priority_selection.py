from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.priority_selection_types import Priority, High, Normal

run = _cott_load("_cott_impl/curriculum/priority_selection/run.py", "ccdc3608c517dee7f3a81995f2b028d54bd9265feb14e6231173f340b900bc75", "run")

__all__ = ["Priority", "High", "Normal", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
