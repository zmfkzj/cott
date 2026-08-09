from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.signed_addition_types import LEFT, RIGHT

run = _cott_load("_cott_impl/curriculum/signed_addition/run.py", "d58b2844407bd65e8fdb768ee662b05e8779b2dec2d92df70dd00a8132f5f238", "run")

__all__ = ["LEFT", "RIGHT", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
