from cott_runtime import CottList, Err, I64, Ok, Result
from curriculum.tic_tac_toe_types import Cell, Cell_Empty, Cell_O, Cell_X, MoveError, MoveError_InvalidBoard, MoveError_InvalidPosition, MoveError_InvalidTurn, MoveError_Occupied, MoveError_Terminal, MoveResult, Outcome_Draw, Outcome_InProgress, Outcome_OWins, Outcome_XWins, Player, Player_O, Player_X


def apply_tic_tac_toe_move(board: CottList[Cell], player: Player, position: I64) -> Result[MoveResult, MoveError]:
    if len(board) != 9:
        return Err(error=MoveError_InvalidBoard())
    if position < 0 or position > 8:
        return Err(error=MoveError_InvalidPosition())

    x_count = sum(1 for cell in board if isinstance(cell, Cell_X))
    o_count = sum(1 for cell in board if isinstance(cell, Cell_O))
    x_wins = (
        (isinstance(board[0], Cell_X) and isinstance(board[1], Cell_X) and isinstance(board[2], Cell_X))
        or (isinstance(board[3], Cell_X) and isinstance(board[4], Cell_X) and isinstance(board[5], Cell_X))
        or (isinstance(board[6], Cell_X) and isinstance(board[7], Cell_X) and isinstance(board[8], Cell_X))
        or (isinstance(board[0], Cell_X) and isinstance(board[3], Cell_X) and isinstance(board[6], Cell_X))
        or (isinstance(board[1], Cell_X) and isinstance(board[4], Cell_X) and isinstance(board[7], Cell_X))
        or (isinstance(board[2], Cell_X) and isinstance(board[5], Cell_X) and isinstance(board[8], Cell_X))
        or (isinstance(board[0], Cell_X) and isinstance(board[4], Cell_X) and isinstance(board[8], Cell_X))
        or (isinstance(board[2], Cell_X) and isinstance(board[4], Cell_X) and isinstance(board[6], Cell_X))
    )
    o_wins = (
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

    is_x_player = isinstance(player, Player_X)
    if is_x_player:
        if x_count != o_count:
            return Err(error=MoveError_InvalidTurn())
        placed_cell = Cell_X()
        next_player = Player_O()
    else:
        if x_count != o_count + 1:
            return Err(error=MoveError_InvalidTurn())
        placed_cell = Cell_O()
        next_player = Player_X()

    if x_wins or o_wins or x_count + o_count == 9:
        return Err(error=MoveError_Terminal())
    if not isinstance(board[position], Cell_Empty):
        return Err(error=MoveError_Occupied())

    moved_board = CottList(values=(placed_cell if index == position else cell for index, cell in enumerate(board)))
    if is_x_player:
        won = (
            (isinstance(moved_board[0], Cell_X) and isinstance(moved_board[1], Cell_X) and isinstance(moved_board[2], Cell_X))
            or (isinstance(moved_board[3], Cell_X) and isinstance(moved_board[4], Cell_X) and isinstance(moved_board[5], Cell_X))
            or (isinstance(moved_board[6], Cell_X) and isinstance(moved_board[7], Cell_X) and isinstance(moved_board[8], Cell_X))
            or (isinstance(moved_board[0], Cell_X) and isinstance(moved_board[3], Cell_X) and isinstance(moved_board[6], Cell_X))
            or (isinstance(moved_board[1], Cell_X) and isinstance(moved_board[4], Cell_X) and isinstance(moved_board[7], Cell_X))
            or (isinstance(moved_board[2], Cell_X) and isinstance(moved_board[5], Cell_X) and isinstance(moved_board[8], Cell_X))
            or (isinstance(moved_board[0], Cell_X) and isinstance(moved_board[4], Cell_X) and isinstance(moved_board[8], Cell_X))
            or (isinstance(moved_board[2], Cell_X) and isinstance(moved_board[4], Cell_X) and isinstance(moved_board[6], Cell_X))
        )
        outcome = Outcome_XWins() if won else Outcome_Draw() if x_count + o_count == 8 else Outcome_InProgress()
    else:
        won = (
            (isinstance(moved_board[0], Cell_O) and isinstance(moved_board[1], Cell_O) and isinstance(moved_board[2], Cell_O))
            or (isinstance(moved_board[3], Cell_O) and isinstance(moved_board[4], Cell_O) and isinstance(moved_board[5], Cell_O))
            or (isinstance(moved_board[6], Cell_O) and isinstance(moved_board[7], Cell_O) and isinstance(moved_board[8], Cell_O))
            or (isinstance(moved_board[0], Cell_O) and isinstance(moved_board[3], Cell_O) and isinstance(moved_board[6], Cell_O))
            or (isinstance(moved_board[1], Cell_O) and isinstance(moved_board[4], Cell_O) and isinstance(moved_board[7], Cell_O))
            or (isinstance(moved_board[2], Cell_O) and isinstance(moved_board[5], Cell_O) and isinstance(moved_board[8], Cell_O))
            or (isinstance(moved_board[0], Cell_O) and isinstance(moved_board[4], Cell_O) and isinstance(moved_board[8], Cell_O))
            or (isinstance(moved_board[2], Cell_O) and isinstance(moved_board[4], Cell_O) and isinstance(moved_board[6], Cell_O))
        )
        outcome = Outcome_OWins() if won else Outcome_Draw() if x_count + o_count == 8 else Outcome_InProgress()
    return Ok(value=MoveResult(board=moved_board, next_player=next_player, outcome=outcome))
