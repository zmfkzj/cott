from real.harlequin.results_types import GridPosition, ResultSet, ResultsGrid


def new_grid(result: ResultSet) -> ResultsGrid:
    return ResultsGrid(
        result=result,
        cursor=GridPosition(row=0, column=0),
        anchor=GridPosition(row=0, column=0),
        first_row=0,
        first_column=0,
    )
