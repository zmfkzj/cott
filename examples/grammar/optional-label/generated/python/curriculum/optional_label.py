from __future__ import annotations

from cott_runtime import _cott_load

run = _cott_load("_cott_impl/curriculum/optional_label/run.py", "03edf60249ec91b3cecf983bc8b6ed2fd662eea27e536808afd1880c55980445", "run")

__all__ = ["run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
