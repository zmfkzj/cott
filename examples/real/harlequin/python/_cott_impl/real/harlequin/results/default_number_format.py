from cott_runtime import CottList, U64

from real.harlequin.results_types import NumberFormat


def default_number_format() -> NumberFormat:
    grouping: list[U64] = []
    return NumberFormat(thousands_separator="", decimal_point=".", grouping=CottList(values=grouping))
