from typing import Final

from cott_runtime import CottList, U16
from real.toolong.help_types import HELP_TITLE
from real.toolong.model_types import StyledSpan, StyledText

_COLORS: Final[str] = "#881177 #aa3355 #cc6666 #ee9944 #eedd00 #99dd55 #44dd88 #22ccbb #00bbcc #0099cc #3366bb #663399"


def help_title(width: U16) -> CottList[StyledText]:
    colors = _COLORS.split(" ")
    lines = HELP_TITLE.splitlines()
    block_width = max(len(line) for line in lines)
    indent = max(0, width - block_width) // 2
    result: list[StyledText] = []
    for index, line in enumerate(lines):
        if line == "":
            result.append(StyledText(text="", spans=CottList(values=[])))
        else:
            span = StyledSpan(start=indent, end=indent + len(line), style="fg:" + colors[index])
            result.append(StyledText(text=" " * indent + line, spans=CottList(values=[span])))
    return CottList(values=result)
