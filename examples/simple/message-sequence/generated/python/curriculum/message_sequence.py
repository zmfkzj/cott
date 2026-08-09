from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.message_sequence_types import Message

run = _cott_load("_cott_impl/curriculum/message_sequence/run.py", "a88d0f29188e2e080f7bd346d7670d420a750245ef9dc86afb62f51f6fdf5a10", "run")

__all__ = ["Message", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
