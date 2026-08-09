from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.access_grant_types import PrincipalId, AccessGrant, Granted, Denied, AccessError, MissingRole

run = _cott_load("_cott_impl/curriculum/access_grant/run.py", "f9d9d81965ae592785fa1bde08355a04363ed163d23c03894dfdefcec892985c", "run")

__all__ = ["PrincipalId", "AccessGrant", "Granted", "Denied", "AccessError", "MissingRole", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
