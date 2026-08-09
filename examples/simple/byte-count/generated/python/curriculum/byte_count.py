from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.byte_count_types import ByteCount

run = _cott_load("_cott_impl/curriculum/byte_count/run.py", "f30a8ad82a86973cecb3d17af44ce47528baae3122d1d3c9f65d37843ab88a9a", "run")

__all__ = ["ByteCount", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
