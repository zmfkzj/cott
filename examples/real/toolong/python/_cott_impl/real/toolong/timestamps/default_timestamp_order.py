from typing import Final

from cott_runtime import U8, CottList

_FORMAT_COUNT: Final[int] = 17


def default_timestamp_order() -> CottList[U8]:
    return CottList(values=list(range(_FORMAT_COUNT)))
