from __future__ import annotations

from typing import TypeAlias, Union

from curriculum.subscription_activation_types import SubscriptionId, Subscription, SubscriptionError, AlreadyActive
class SubscriptionId: ...

class Subscription: ...

SubscriptionError: TypeAlias = Union[AlreadyActive]

def run() -> Result[Subscription, SubscriptionError]: ...
