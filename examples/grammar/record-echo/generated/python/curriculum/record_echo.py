from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.record_echo_types import Message

run = _cott_load("_cott_impl/curriculum/record_echo/run.py", "5c635f4e522e253d7a79f8bf9cfdbcde77f18e7f6dff4be80ec4be05de3bfca5", "run")

__all__ = ["Message", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
