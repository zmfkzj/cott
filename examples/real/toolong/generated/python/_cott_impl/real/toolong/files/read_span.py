import os
from typing import Final

from cott_runtime import CottContractViolation, Err, Some, _cott_fixture_read
from real.toolong.files import decompress
from real.toolong.model_types import ByteSpan, LogSource

_INACTIVE: Final[str] = "fixture adapters are inactive"


def read_span(source: LogSource, span: ByteSpan) -> bytes:
    start = span.start
    end = span.end
    if start >= end:
        return b""
    descriptor = source.descriptor
    if isinstance(descriptor, Some):
        try:
            return os.pread(descriptor.value, end - start, start)
        except (OSError, OverflowError, ValueError):
            return b""
    else:
        try:
            raw = _cott_fixture_read(source.path)
        except CottContractViolation as error:
            if error.message == _INACTIVE or isinstance(error.__cause__, OSError):
                return b""
            raise
        except OSError:
            return b""
        content = decompress(raw, source.compression)
        if isinstance(content, Err):
            return b""
        return content.value[start:end]
