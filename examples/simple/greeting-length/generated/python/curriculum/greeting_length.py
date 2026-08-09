from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.greeting_length_types import GREETING

run = _cott_load("_cott_impl/curriculum/greeting_length/run.py", "80a123e5ec05ca053e39c43fd1fd3989d452a4345dc2830f8e04f6854d5523f8", "run")

__all__ = ["GREETING", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
