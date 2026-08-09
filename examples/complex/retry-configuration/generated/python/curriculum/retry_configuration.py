from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.retry_configuration_types import RetryCount, RetryConfiguration

run = _cott_load("_cott_impl/curriculum/retry_configuration/run.py", "907c0ebba23ee11554f89eff30021cbf1720a100105a16770871dfea37df9f70", "run")

__all__ = ["RetryCount", "RetryConfiguration", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
