from cott_runtime import CottList, Err, Ok, Result, UNIT, Unit
from curriculum.tic_tac_toe_types import Cell, Cell_O, Cell_X, MoveError, MoveError_InvalidBoard


def validate_board_state(board: CottList[Cell]) -> Result[Unit, MoveError]:
    if len(board) != 9:
        return Err(error=MoveError_InvalidBoard())

    x_count: int = sum(1 for cell in board if isinstance(cell, Cell_X))
    o_count: int = sum(1 for cell in board if isinstance(cell, Cell_O))
    x_wins: bool = (
        (isinstance(board[0], Cell_X) and isinstance(board[1], Cell_X) and isinstance(board[2], Cell_X))
        or (isinstance(board[3], Cell_X) and isinstance(board[4], Cell_X) and isinstance(board[5], Cell_X))
        or (isinstance(board[6], Cell_X) and isinstance(board[7], Cell_X) and isinstance(board[8], Cell_X))
        or (isinstance(board[0], Cell_X) and isinstance(board[3], Cell_X) and isinstance(board[6], Cell_X))
        or (isinstance(board[1], Cell_X) and isinstance(board[4], Cell_X) and isinstance(board[7], Cell_X))
        or (isinstance(board[2], Cell_X) and isinstance(board[5], Cell_X) and isinstance(board[8], Cell_X))
        or (isinstance(board[0], Cell_X) and isinstance(board[4], Cell_X) and isinstance(board[8], Cell_X))
        or (isinstance(board[2], Cell_X) and isinstance(board[4], Cell_X) and isinstance(board[6], Cell_X))
    )
    o_wins: bool = (
        (isinstance(board[0], Cell_O) and isinstance(board[1], Cell_O) and isinstance(board[2], Cell_O))
        or (isinstance(board[3], Cell_O) and isinstance(board[4], Cell_O) and isinstance(board[5], Cell_O))
        or (isinstance(board[6], Cell_O) and isinstance(board[7], Cell_O) and isinstance(board[8], Cell_O))
        or (isinstance(board[0], Cell_O) and isinstance(board[3], Cell_O) and isinstance(board[6], Cell_O))
        or (isinstance(board[1], Cell_O) and isinstance(board[4], Cell_O) and isinstance(board[7], Cell_O))
        or (isinstance(board[2], Cell_O) and isinstance(board[5], Cell_O) and isinstance(board[8], Cell_O))
        or (isinstance(board[0], Cell_O) and isinstance(board[4], Cell_O) and isinstance(board[8], Cell_O))
        or (isinstance(board[2], Cell_O) and isinstance(board[4], Cell_O) and isinstance(board[6], Cell_O))
    )

    if x_count < o_count or x_count > o_count + 1:
        return Err(error=MoveError_InvalidBoard())
    if (x_wins and o_wins) or (x_wins and x_count != o_count + 1) or (o_wins and x_count != o_count):
        return Err(error=MoveError_InvalidBoard())
    return Ok(value=UNIT)
