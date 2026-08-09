from __future__ import annotations

from cott_runtime import _cott_load

from curriculum.subscription_activation_types import SubscriptionId, Subscription, SubscriptionError, AlreadyActive

run = _cott_load("_cott_impl/curriculum/subscription_activation/run.py", "b574aeacb17a97075c8bc8b0721150cb644db0cfcb47de1a39a7420186426f41", "run")

__all__ = ["SubscriptionId", "Subscription", "SubscriptionError", "AlreadyActive", "run"]

if __name__ == "__main__":
    from cott_runtime import _cott_display
    print(_cott_display(run()))
