from __future__ import annotations

from cott_runtime import _cott_load

run = _cott_load("_cott_impl/curriculum/unit_echo/run.py", "2f6d22b91678399f9cc058aedae1460fb66f887759b05f07c493740ba55d59dc", "run")

__all__ = ["run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
