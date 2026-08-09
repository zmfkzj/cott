from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.named_timestamp_types import Timestamp

run = _cott_load("_cott_impl/curriculum/named_timestamp/run.py", "8956be27b3706d8fc9fe225d3858b0b1f13278cbc0e25e86da6e0e8089df5e79", "run")

__all__ = ["Timestamp", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
