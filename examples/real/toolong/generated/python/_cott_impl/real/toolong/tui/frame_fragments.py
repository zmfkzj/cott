from cott_runtime import CottList
from real.toolong.model_types import ScreenRow
from real.toolong.tui_types import Fragment


def frame_fragments(row: ScreenRow) -> CottList[Fragment]:
    fragments: list[Fragment] = []
    for run in row.runs:
        fragments.append(Fragment(style=run.style, text=run.text))
    return CottList(values=fragments)
