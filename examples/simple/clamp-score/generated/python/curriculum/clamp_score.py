from __future__ import annotations

from cott_runtime import _cott_load

run = _cott_load("_cott_impl/curriculum/clamp_score/run.py", "d2d2a951b11a1e001a1778f6452bbafad4981f43d655387579f0b59bb1cf155e", "run")

__all__ = ["run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
