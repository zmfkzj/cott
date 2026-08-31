from cott_runtime import CottList, Err, Result
from real.pgcli_types import (
    ClientError,
    ClientError_NotificationFailed,
    Notification,
    NotificationRequest,
)


def receive_notifications(request: NotificationRequest) -> Result[CottList[Notification], ClientError]:
    return Err(
        error=ClientError_NotificationFailed(
            message="notifications require an unavailable database.read host binding",
        )
    )
