from cott_runtime import Ok, Result
from curriculum.subscription_activation_types import (
    Subscription,
    SubscriptionError,
    SubscriptionId,
)


def run() -> Result[Subscription, SubscriptionError]:
    return Ok(value=Subscription(id=SubscriptionId(value=42), active=True))
