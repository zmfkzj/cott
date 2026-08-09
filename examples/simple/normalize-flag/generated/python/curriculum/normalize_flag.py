from __future__ import annotations

from cott_runtime import _cott_load

run = _cott_load("_cott_impl/curriculum/normalize_flag/run.py", "0fe323f985812a2e8b1aae309313a44eff71241c3221daf906e619c2b58d5a33", "run")

__all__ = ["run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
