from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.increment_count_types import START

run = _cott_load("_cott_impl/curriculum/increment_count/run.py", "0569e9c1be12450f519cdecd05bd6f65026ac2fb40a5fd9d74d6f24d364f35fa", "run")

__all__ = ["START", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
