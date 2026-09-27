from real.harlequin.results import format_number_text
from real.harlequin.results_types import NumberFormat, ResultSet


def results_title(result: ResultSet, number_format: NumberFormat) -> str:
    if result.row_count == 0 and result.fetched_row_count == 0:
        return "Query Returned No Records"
    fetched = format_number_text(str(result.fetched_row_count), number_format)
    if result.truncated:
        shown = format_number_text(str(result.row_count), number_format)
        return f"Query Results (Showing {shown} of >{fetched} Records)"
    if result.row_count < result.fetched_row_count:
        shown = format_number_text(str(result.row_count), number_format)
        return f"Query Results (Showing {shown} of {fetched} Records)"
    return f"Query Results ({fetched} Records)"
