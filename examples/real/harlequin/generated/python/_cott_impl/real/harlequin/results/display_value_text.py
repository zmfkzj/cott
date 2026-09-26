import math

from real.harlequin.results import format_number_text
from real.harlequin.results_types import CellValue, CellValue_Blob, CellValue_Boolean, CellValue_Integer, CellValue_Null, CellValue_Real, CellValue_Text, NumberFormat


def display_value_text(value: CellValue, number_format: NumberFormat, id_column: bool) -> str:
    if isinstance(value, CellValue_Null):
        return "∅ null"
    if isinstance(value, CellValue_Boolean):
        return "✓ True" if value.value else "X False"
    if isinstance(value, CellValue_Integer):
        digits = str(value.value)
        return digits if id_column else format_number_text(digits, number_format)
    if isinstance(value, CellValue_Real):
        text = format(value.value, "g")
        if math.isnan(value.value) or math.isinf(value.value):
            return text
        return format_number_text(text, number_format)
    if isinstance(value, CellValue_Text):
        raw = value.value
        cut = len(raw)
        for index, char in enumerate(raw):
            if char == "\r" or char == "\n":
                cut = index
                break
        if cut < len(raw):
            return raw[:cut] + "…⏎"
        return raw
    blob: CellValue_Blob = value
    data = blob.value
    shown = repr(data[:32])
    if len(data) > 32:
        return f"{shown} (+{len(data) - 32} bytes)"
    return shown
