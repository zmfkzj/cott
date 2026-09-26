import contextlib
from typing import Any

from cott_runtime import UNIT, Some, Unit
from real.pgcli.connection_types import Executor


def stop_executor_tunnel(executor: Executor) -> Unit:
    tunnel_option = executor.tunnel
    if isinstance(tunnel_option, Some):
        forwarder: Any = tunnel_option.value.unwrap()
        with contextlib.suppress(Exception):
            forwarder.stop()
    return UNIT
