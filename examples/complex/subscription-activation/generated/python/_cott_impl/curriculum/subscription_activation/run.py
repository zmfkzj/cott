from cott_runtime import Ok
from curriculum.subscription_activation_types import Subscription, SubscriptionId


def run() -> Ok[Subscription]:
    return Ok(value=Subscription(id=SubscriptionId(value=42), active=True))
