from cott_runtime import Err, Ok, Result, UNIT, Unit
from curriculum.move_2048_types import Board4, Move2048Error, Move2048Error_InvalidBoardSize, Move2048Error_InvalidTile


def validate_2048_board(board: Board4) -> Result[Unit, Move2048Error]:
    if len(board.cells) != 16:
        return Err(error=Move2048Error_InvalidBoardSize())

    for tile in board.cells:
        if tile < 0 or tile > 0xFFFF or (tile != 0 and tile & (tile - 1) != 0):
            return Err(error=Move2048Error_InvalidTile())

    return Ok(value=UNIT)
