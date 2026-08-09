from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.profile_summary_types import ProfileSummary

run = _cott_load("_cott_impl/curriculum/profile_summary/run.py", "11fa76d64fff448abe457abb2960e9881e7dcd6d88d8544e594da602b36e8dc8", "run")

__all__ = ["ProfileSummary", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
