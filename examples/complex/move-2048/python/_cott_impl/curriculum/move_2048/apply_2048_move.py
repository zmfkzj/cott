from cott_runtime import CottList, Err, Ok, Result, U16, U32
from curriculum.move_2048_types import Board4, Direction_Down, Direction_Left, Direction_Right, Move2048Error, Move2048Error_InvalidBoardSize, Move2048Error_InvalidTile, Move2048Error_ScoreOverflow, MoveRequest, MoveResult


def apply_2048_move(request: MoveRequest) -> Result[MoveResult, Move2048Error]:
    cells: CottList[U16] = request.board.cells
    if len(cells) != 16:
        return Err(error=Move2048Error_InvalidBoardSize())

    for tile in cells:
        if tile < 0 or tile > 0xFFFF or (tile != 0 and tile & (tile - 1) != 0):
            return Err(error=Move2048Error_InvalidTile())

    moved_cells: list[U16] = [0] * 16
    total_score: U32 = 0
    changed: bool = False

    for line_number in range(4):
        indices: list[int] = []
        if isinstance(request.direction, Direction_Left):
            for column in range(4):
                indices.append(line_number * 4 + column)
        elif isinstance(request.direction, Direction_Right):
            for column in range(3, -1, -1):
                indices.append(line_number * 4 + column)
        elif isinstance(request.direction, Direction_Down):
            for row in range(3, -1, -1):
                indices.append(row * 4 + line_number)
        else:
            for row in range(4):
                indices.append(row * 4 + line_number)

        compacted: list[U16] = []
        for index in indices:
            tile = cells[index]
            if tile != 0:
                compacted.append(tile)

        merged: list[U16] = []
        compacted_index: int = 0
        while compacted_index < len(compacted):
            tile = compacted[compacted_index]
            if compacted_index + 1 < len(compacted) and tile == compacted[compacted_index + 1]:
                merged_tile: U16 = tile * 2
                if merged_tile > 0xFFFF:
                    return Err(error=Move2048Error_ScoreOverflow())
                if total_score > 0xFFFFFFFF - merged_tile:
                    return Err(error=Move2048Error_ScoreOverflow())
                total_score += merged_tile
                merged.append(merged_tile)
                compacted_index += 2
            else:
                merged.append(tile)
                compacted_index += 1

        while len(merged) < 4:
            merged.append(0)

        for offset in range(4):
            value = merged[offset]
            index = indices[offset]
            moved_cells[index] = value
            if value != cells[index]:
                changed = True

    return Ok(value=MoveResult(board=Board4(cells=CottList(values=moved_cells)), score_gain=total_score, changed=changed))
