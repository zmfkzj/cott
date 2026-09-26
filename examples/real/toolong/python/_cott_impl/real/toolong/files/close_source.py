import os

from cott_runtime import Some, UNIT, Unit
from real.toolong.model_types import LogSource


def close_source(source: LogSource) -> Unit:
    descriptor = source.descriptor
    if isinstance(descriptor, Some):
        try:
            os.close(descriptor.value)
        except OSError:
            return UNIT
        return UNIT
    else:
        return UNIT
