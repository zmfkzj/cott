import decimal
import json
from collections.abc import Iterator
from typing import Any, cast

import cli_helpers.utils
import tabulate
from cli_helpers.tabular_output import (
    delimited_output_adapter,
    json_output_adapter,
    preprocessors,
    tabulate_adapter,
    tsv_output_adapter,
    vertical_table_adapter,
)
from cott_runtime import Err, Ok, Option, Result, Some

from real.pgcli.completion import apply_identifier_casing
from real.pgcli.output import style_text, table_format_names, visualize_explain_plans
from real.pgcli.output_types import FormattedOutput, OutputError, OutputError_Failed, OutputSettings, OutputStyle, ResultSet
from real.pgcli.parseutils import extract_tables


def _rank(value: object) -> int:
    if value is None:
        return 0
    if type(value) is int:
        return 2
    if isinstance(value, (float, decimal.Decimal)):
        return 3
    if isinstance(value, bytes):
        return 4
    return 5


def _column_types(rows: list[tuple[object, ...]]) -> list[type]:
    ranks: list[int] = []
    for row in rows:
        for index, value in enumerate(row):
            rank = _rank(value)
            if index == len(ranks):
                ranks.append(rank)
            elif rank > ranks[index]:
                ranks[index] = rank
    types: dict[int, type] = {0: type(None), 2: int, 3: decimal.Decimal, 4: bytes, 5: str}
    return [types[rank] for rank in ranks]


def _format_array(value: object, missing: str) -> object:
    if value is None:
        return missing
    if isinstance(value, list):
        return "{" + ",".join(str(_format_array(item, missing)) for item in cast(list[object], value)) + "}"
    return value


def _array_cell(value: object, missing: str) -> object:
    if isinstance(value, list):
        return _format_array(cast(list[object], value), missing)
    return value


def _style_of(settings: OutputSettings) -> OutputStyle | None:
    style = settings.style
    return style.value if isinstance(style, Some) else None


def _null_step(data: Any, settings: OutputSettings) -> list[list[object]]:
    style = _style_of(settings)
    missing = settings.missing_value
    if style is not None:
        missing = style_text(missing, style.null, style.base, style.true_color)
    return [[missing if value is None else value for value in cast(list[object], list(row))] for row in data]


def _style_rows(data: Any, headers: list[str], settings: OutputSettings) -> tuple[Any, list[str]]:
    style = _style_of(settings)
    if style is None:
        return data, headers
    if style.header:
        headers = [style_text(header, style.header, style.base, style.true_color) for header in headers]
    if style.odd_row or style.even_row:
        styled: list[list[str]] = []
        for index, row in enumerate(data, start=1):
            definition = style.odd_row if index % 2 else style.even_row
            styled.append([style_text(str(value), definition, style.base, style.true_color) for value in cast(list[object], list(row))])
        data = styled
    return data, headers


def _literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bytes):
        return "X'" + value.hex() + "'"
    return "'" + str(value) + "'"


def _adapter(data: list[list[object]], headers: list[str], table_format: str, query: str) -> Iterator[str]:
    table = "DUAL"
    for first in extract_tables(query):
        schema = first.schema
        table = schema.value + "." + first.name if isinstance(schema, Some) and schema.value else first.name
        break
    if table_format == "sql-insert":
        yield 'INSERT INTO "' + table + '" ("' + '", "'.join(headers) + '") VALUES'
        prefix = "  "
        for row in data:
            yield prefix + "(" + ", ".join(_literal(value) for value in row) + ")"
            prefix = ", "
        yield ";"
        return
    keys = 2 if table_format == "sql-update-2" else 1
    for row in data:
        yield 'UPDATE "' + table + '" SET'
        prefix = "  "
        for index in range(keys, len(row)):
            yield prefix + '"' + headers[index] + '" = ' + _literal(row[index])
            prefix = ", "
        yield "WHERE " + " AND ".join('"' + headers[index] + '" = ' + _literal(row[index]) for index in range(keys)) + ";"


def _render(fmt: str, rows: list[tuple[object, ...]], headers: list[str], settings: OutputSettings) -> list[str]:
    if not fmt or fmt not in table_format_names():
        raise ValueError('unrecognized format "' + (fmt or "None") + '"')
    types = _column_types(rows)
    field_width = settings.max_field_width
    options: dict[str, Any] = {
        "sep_title": "RECORD {n}",
        "sep_character": "-",
        "sep_length": (1, 25),
        "missing_value": settings.missing_value,
        "integer_format": settings.decimal_format,
        "float_format": settings.float_format,
        "column_date_formats": dict(settings.column_date_formats.items()),
        "disable_numparse": True,
        "preserve_whitespace": True,
        "max_field_width": field_width.value if isinstance(field_width, Some) else None,
    }
    pre: Any = preprocessors
    data: Any = rows
    names: Any = list(headers)
    if settings.float_format == "":
        data, names = pre.align_decimals(data, names, column_types=types, **options)
    else:
        data, names = pre.format_numbers(data, names, column_types=types, **options)
        data = [[_array_cell(value, settings.missing_value) for value in cast(list[object], list(row))] for row in data]
    if options["column_date_formats"]:
        data, names = pre.format_timestamps(data, names, column_types=types, **options)
    header_names = [str(name) for name in cast(list[object], list(names))]
    output: Any
    adapter: Any
    if fmt == "vertical":
        data = _null_step(data, settings)
        data, names = pre.convert_to_string(data, header_names, column_types=types, **options)
        data, header_names = _style_rows(list(data), [str(name) for name in names], settings)
        adapter = vertical_table_adapter
        output = adapter.adapter(list(data), header_names, sep_title="RECORD {n}", sep_character="-", sep_length=(1, 25))
    elif fmt in ("csv", "csv-tab", "csv-noheader", "csv-tab-noheader"):
        data = _null_step(data, settings)
        data, names = pre.bytes_to_string(data, header_names, column_types=types, **options)
        adapter = delimited_output_adapter
        if fmt == "csv":
            output = adapter.adapter(list(data), names, table_format=fmt, dialect="unix")
        else:
            output = adapter.adapter(list(data), names, table_format=fmt)
    elif fmt in ("tsv", "tsv_noheader"):
        data = _null_step(data, settings)
        data, names = pre.bytes_to_string(data, header_names, column_types=types, **options)
        data, names = pre.convert_to_string(data, names, column_types=types, **options)
        adapter = tsv_output_adapter
        output = adapter.adapter(list(data), names, table_format=fmt)
    elif fmt in ("jsonl", "jsonl_escaped"):
        data, names = pre.bytes_to_string(data, header_names, column_types=types, **options)
        adapter = json_output_adapter
        output = adapter.adapter(list(data), names, table_format=fmt)
    elif fmt in ("sql-insert", "sql-update", "sql-update-1", "sql-update-2"):
        output = _adapter([cast(list[object], list(row)) for row in data], header_names, fmt, settings.query)
    else:
        data = _null_step(data, settings)
        data, names = pre.convert_to_string(data, header_names, column_types=types, **options)
        data, names = pre.truncate_string(data, names, max_field_width=options["max_field_width"])
        data, header_names = _style_rows(list(data), [str(name) for name in names], settings)
        tb: Any = tabulate
        if not tb.multiline_formats.get(fmt):
            data, header_names = pre.escape_newlines(data, header_names)
        adapter = tabulate_adapter
        style = _style_of(settings)
        if style is not None and fmt in adapter.supported_table_formats:
            original: Any = tb._table_formats[fmt]
            fields: list[Any] = []
            for field in original:
                if type(field) is tb.Line or type(field) is tb.DataRow:
                    fields.append(type(field)(*[style_text(str(part), style.table_separator, style.base, style.true_color) for part in field]))
                else:
                    fields.append(field)
            tb._table_formats[fmt] = tb.TableFormat(*fields)
            try:
                output = list(adapter.adapter(list(data), header_names, table_format=fmt, preserve_whitespace=True, disable_numparse=True))
            finally:
                tb._table_formats[fmt] = original
        else:
            output = adapter.adapter(list(data), header_names, table_format=fmt, preserve_whitespace=True, disable_numparse=True)
    return [str(item) for item in cast(list[object], list(output))]


def _plan_text(value: object) -> str:
    if isinstance(value, str):
        return value
    json.loads(cast(Any, value))
    kind = "bytes" if isinstance(value, bytes) else "bytearray"
    raise TypeError("the JSON object must be str, bytes or bytearray, not " + kind)


def _failed(message: str) -> Result[FormattedOutput, OutputError]:
    return Err(error=OutputError_Failed(message=message))


def format_output(title: Option[str], result_set: Option[ResultSet], status: Option[str], settings: OutputSettings, explain_mode: bool) -> Result[FormattedOutput, OutputError]:
    try:
        fmt = "plain" if settings.tuples_only else ("vertical" if settings.expanded else settings.table_format)
        expanded_view = settings.expanded or settings.table_format == "vertical"
        if not explain_mode and fmt and fmt not in table_format_names():
            return _failed('unrecognized format_name "' + fmt + '"')
        items: list[str] = []
        count = 0
        if isinstance(title, Some) and title.value and not settings.tuples_only:
            items.append(title.value)
            count += 1
        result = result_set.value if isinstance(result_set, Some) else None
        width = settings.max_width
        if result is not None:
            rows = cast(list[tuple[object, ...]], result.rows.unwrap())
            if result.rowcount >= 0 or rows:
                headers: list[str] = []
                if not settings.tuples_only:
                    casing = settings.header_casing
                    headers = [apply_identifier_casing(casing.value, name) if isinstance(casing, Some) else name for name in result.columns]
                if explain_mode:
                    [(value,)] = rows
                    text = _plan_text(value)
                    plan_width = width.value if isinstance(width, Some) and width.value != 0 else 100
                    plan = visualize_explain_plans(text, plan_width)
                    if isinstance(plan, Err):
                        return plan
                    formatted = plan.value
                    if formatted.items == 0:
                        return _failed("")
                    items.append(formatted.text)
                    count += formatted.items
                else:
                    section = _render(fmt, rows, headers, settings)
                    if not section:
                        return _failed("")
                    helpers: Any = cli_helpers.utils
                    if not expanded_view and isinstance(width, Some) and width.value > 0 and headers and len(str(helpers.strip_ansi(section[0]))) > width.value:
                        section = _render("vertical", rows, headers, settings)
                    items.extend(section)
                    count += len(section)
        if isinstance(status, Some) and status.value and not settings.tuples_only:
            footer = status.value
            if result is not None and result.rowcount >= 0 and not isinstance(width, Some) and not footer.endswith(str(result.rowcount)):
                footer += " " + str(result.rowcount)
            items.append(footer)
            count += 1
        return Ok(value=FormattedOutput(text="\n".join(items), items=count))
    except Exception as error:
        return _failed(str(error))
