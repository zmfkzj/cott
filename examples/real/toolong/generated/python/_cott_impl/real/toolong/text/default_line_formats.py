from cott_runtime import CottList
from real.toolong.model_types import LineFormat, LineFormat_CombinedLog, LineFormat_CommonLog, LineFormat_Json, LineFormat_Plain


def default_line_formats() -> CottList[LineFormat]:
    return CottList(values=[LineFormat_Json(), LineFormat_CommonLog(), LineFormat_CombinedLog(), LineFormat_Plain()])
