from cott_runtime import U64

from real.harlequin.results_types import GridMotion, GridMotion_ColumnEnd, GridMotion_ColumnStart, GridMotion_Down, GridMotion_Left, GridMotion_NextCell, GridMotion_PageDown, GridMotion_PageUp, GridMotion_PreviousCell, GridMotion_Right, GridMotion_RowEnd, GridMotion_RowStart, GridMotion_SelectAll, GridMotion_TableStart, GridMotion_Up, GridPosition, ResultsGrid


def move_grid(grid: ResultsGrid, motion: GridMotion, extend: bool, page_rows: U64) -> ResultsGrid:
    rows = grid.result.row_count
    columns = len(grid.result.columns)
    if rows == 0 or columns == 0:
        return grid
    last_row = rows - 1
    last_column = columns - 1
    row = min(grid.cursor.row, last_row)
    column = min(grid.cursor.column, last_column)
    page = max(page_rows, 1)
    if isinstance(motion, GridMotion_SelectAll):
        return ResultsGrid(result=grid.result, cursor=GridPosition(row=last_row, column=last_column), anchor=GridPosition(row=0, column=0), first_row=grid.first_row, first_column=grid.first_column)
    if isinstance(motion, GridMotion_Up):
        row = max(row - 1, 0)
    elif isinstance(motion, GridMotion_Down):
        row = min(row + 1, last_row)
    elif isinstance(motion, GridMotion_Left):
        column = max(column - 1, 0)
    elif isinstance(motion, GridMotion_Right):
        column = min(column + 1, last_column)
    elif isinstance(motion, GridMotion_RowStart):
        column = 0
    elif isinstance(motion, GridMotion_RowEnd):
        column = last_column
    elif isinstance(motion, GridMotion_ColumnStart):
        row = 0
    elif isinstance(motion, GridMotion_ColumnEnd):
        row = last_row
    elif isinstance(motion, GridMotion_NextCell):
        if column < last_column:
            column += 1
        elif row < last_row:
            row += 1
            column = 0
    elif isinstance(motion, GridMotion_PreviousCell):
        if column > 0:
            column -= 1
        elif row > 0:
            row -= 1
            column = last_column
    elif isinstance(motion, GridMotion_PageUp):
        row = max(row - page, 0)
    elif isinstance(motion, GridMotion_PageDown):
        row = min(row + page, last_row)
    elif isinstance(motion, GridMotion_TableStart):
        row = 0
        column = 0
    else:
        row = last_row
        column = last_column
    cursor = GridPosition(row=row, column=column)
    anchor = grid.anchor if extend else cursor
    return ResultsGrid(result=grid.result, cursor=cursor, anchor=anchor, first_row=grid.first_row, first_column=grid.first_column)
