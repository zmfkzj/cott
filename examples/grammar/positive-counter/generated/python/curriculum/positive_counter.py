from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.positive_counter_types import PositiveCount

run = _cott_load("_cott_impl/curriculum/positive_counter/run.py", "38bdab7d79e8b93c066e036bd3c107ccbf40ee71d0d7c93ad453bb576a4b9725", "run")

__all__ = ["PositiveCount", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
