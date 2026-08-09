from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.nonempty_name_types import NonemptyName

run = _cott_load("_cott_impl/curriculum/nonempty_name/run.py", "b2ab50bfdca1240ca2413f32b25b2c370c4c32ce499f793ebd54fc9d72e56714", "run")

__all__ = ["NonemptyName", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
