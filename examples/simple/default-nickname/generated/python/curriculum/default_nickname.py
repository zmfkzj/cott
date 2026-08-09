from __future__ import annotations

from cott_runtime import _cott_load

run = _cott_load("_cott_impl/curriculum/default_nickname/run.py", "304dbd1f7ff4b2608d6be37a770097f387a7008de3acb9cebfdd8344eb49c61b", "run")

__all__ = ["run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
