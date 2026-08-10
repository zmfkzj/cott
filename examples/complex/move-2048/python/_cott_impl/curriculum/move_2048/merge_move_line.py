from cott_runtime import CottList, Err, Ok, Result, U16, U32
from curriculum.move_2048_types import LineMove, Move2048Error, Move2048Error_ScoreOverflow


def merge_move_line(line: CottList[U16]) -> Result[LineMove, Move2048Error]:
    merged_cells: list[U16] = [0] * len(line)
    score_gain: U32 = 0
    write_index: int = 0
    pending: U16 = 0
    has_pending: bool = False

    for tile in line:
        if tile == 0:
            continue
        if not has_pending:
            pending = tile
            has_pending = True
        elif pending == tile:
            merged_tile: U16 = pending * 2
            if merged_tile > 0xFFFF or score_gain > 0xFFFFFFFF - merged_tile:
                return Err(error=Move2048Error_ScoreOverflow())
            merged_cells[write_index] = merged_tile
            write_index += 1
            score_gain += merged_tile
            has_pending = False
        else:
            merged_cells[write_index] = pending
            write_index += 1
            pending = tile

    if has_pending:
        merged_cells[write_index] = pending

    return Ok(value=LineMove(cells=CottList(values=merged_cells), score_gain=score_gain))
