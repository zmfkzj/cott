from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.parity_classification_types import Parity, Even, Odd

run = _cott_load("_cott_impl/curriculum/parity_classification/run.py", "299a8fc53401e32ee57a71989e5137454f81acb7995b3c56076c9d9989b2cd19", "run")

__all__ = ["Parity", "Even", "Odd", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
