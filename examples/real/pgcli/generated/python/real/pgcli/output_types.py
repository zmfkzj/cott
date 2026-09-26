from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
"""The row values of one statement result, kept as the Python objects the executor obtained:
a Python list with one tuple per row, each holding the Python values of that row in column
order, exactly as psycopg returned them after pgcli's text loaders (date, time, timestamp,
timestamptz, bytea, json and jsonb arrive as str) or as a pgspecial command listed them:
None, bool, int, float, decimal.Decimal, str, list (arrays, possibly nested), bytes or any
other object (for example datetime.timedelta or uuid.UUID). Opaque so that large results
are not validated value by value."""
ResultRows: TypeAlias = Opaque[Literal["pgcli.result-rows"]]

"""A scenario-friendly spelling of one Python row value, converted by result_rows_from_cells."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Null:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Text:
    __hash__ = None
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Integer:
    __hash__ = None
    value: I64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Float:
    __hash__ = None
    value: F64

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Decimal:
    __hash__ = None
    value: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Boolean:
    __hash__ = None
    value: bool

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Array:
    __hash__ = None
    items: CottList[Cell]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Cell_Other:
    __hash__ = None
    value: str

Cell: TypeAlias = Union[Cell_Null, Cell_Text, Cell_Integer, Cell_Float, Cell_Decimal, Cell_Boolean, Cell_Array, Cell_Other]

"""The rows of one statement result. columns are the column names (cursor.description
names) and rows the row values in order. type_names are the psycopg type names per column
("" when unknown); they do not influence formatting (upstream derives column types from
cursor.description but that value never reaches the formatter). rowcount says where the
rows came from: >= 0 is the cursor.rowcount of a psycopg cursor (including pgspecial
commands that return a cursor), -1 means the rows came from a plain Python list (pgspecial
list results) or from a row-limited slice of a cursor."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class ResultSet:
    __hash__ = None
    columns: CottList[str]
    type_names: CottList[str]
    rows: Opaque[Literal["pgcli.result-rows"]]
    rowcount: I64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "columns", _cott_validate_abi(self.columns, CottList[str], path="$.columns"))
        if not _cott_validated_construction():
            object.__setattr__(self, "type_names", _cott_validate_abi(self.type_names, CottList[str], path="$.type_names"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rows", _cott_validate_abi(self.rows, Opaque[Literal["pgcli.result-rows"]], path="$.rows"))
        if not _cott_validated_construction():
            object.__setattr__(self, "rowcount", _cott_validate_abi(self.rowcount, I64, path="$.rowcount"))

"""What format_output produced: text is the output items joined with "\\n" ("" when there
are no items) and items is how many items there were. An item may itself contain line
feeds (a vertical record, a CSV field with a newline, a whole explain plan)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class FormattedOutput:
    __hash__ = None
    text: str
    items: U64

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "text", _cott_validate_abi(self.text, str, path="$.text"))
        if not _cott_validated_construction():
            object.__setattr__(self, "items", _cott_validate_abi(self.items, U64, path="$.items"))

"""pgcli's colored-table output style (pgstyle.style_factory_output), as pygments style
definition strings. header, odd_row, even_row and null are the [colors] values of
output.header, output.odd-row, output.even-row and output.null ("" when absent; the
default pgclirc has "#00ff5f bold", "", "" and "#808080"). table_separator is the [colors]
value of "Token.Output.TableSeparator" ("" when absent). base is the definition of the root
pygments Token in the syntax style named by [main] syntax_style
(pygments.styles.get_style_by_name(name).styles.get(Token, ""), the "native" style when
the name is unknown): "" for "default", "#d0d0d0" for "native". Every output token
inherits base. true_color is whether the COLORTERM environment variable, lower-cased,
contains "truecolor" (cli_helpers then uses TerminalTrueColorFormatter instead of
Terminal256Formatter). The defaults are pgcli's default [colors] with syntax_style default."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OutputStyle:
    __hash__ = None
    base: str = ""
    header: str = "#00ff5f bold"
    odd_row: str = ""
    even_row: str = ""
    null: str = "#808080"
    table_separator: str = ""
    true_color: bool = False

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "base", _cott_validate_abi(self.base, str, path="$.base"))
        if not _cott_validated_construction():
            object.__setattr__(self, "header", _cott_validate_abi(self.header, str, path="$.header"))
        if not _cott_validated_construction():
            object.__setattr__(self, "odd_row", _cott_validate_abi(self.odd_row, str, path="$.odd_row"))
        if not _cott_validated_construction():
            object.__setattr__(self, "even_row", _cott_validate_abi(self.even_row, str, path="$.even_row"))
        if not _cott_validated_construction():
            object.__setattr__(self, "null", _cott_validate_abi(self.null, str, path="$.null"))
        if not _cott_validated_construction():
            object.__setattr__(self, "table_separator", _cott_validate_abi(self.table_separator, str, path="$.table_separator"))
        if not _cott_validated_construction():
            object.__setattr__(self, "true_color", _cott_validate_abi(self.true_color, bool, path="$.true_color"))

_cott_default_OutputSettings_max_width: Final[Option[U32]] = Nothing()
_cott_default_OutputSettings_header_casing: Final[Option[Opaque[Literal["pgcli.completion-catalog"]]]] = Nothing()
_cott_default_OutputSettings_style: Final[Option[OutputStyle]] = Nothing()
"""pgcli's OutputSettings for one format_output call. table_format is the current table
format name ([main] table_format or the \\T choice). decimal_format and float_format are
[data_formats] decimal and float ("" = unset). column_date_formats maps a column header to
a strftime format ([column_date_formats]). missing_value is the NULL display string
([main] null_string, default "<null>"). expanded is \\x or [main] expand. max_width is the
terminal width in columns when auto-expand (\\x auto or [main] auto_expand) is on, Nothing
otherwise. header_casing is Some(the completer's catalog) when [main]
case_column_headers is on, Nothing otherwise. style is the colored-output style (the REPL
always passes one). max_field_width is [main] max_field_width (Nothing = no truncation).
tuples_only is -t/--tuples-only. query is the whole command text being executed (used to
find the table name of the sql-insert and sql-update formats). The defaults are those of
upstream's OutputSettings namedtuple (whose max_field_width default is Some(500) and
column_date_formats default is empty)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OutputSettings:
    __hash__ = None
    table_format: str
    column_date_formats: FrozenMap[str, str]
    max_field_width: Option[U32]
    decimal_format: str = ""
    float_format: str = ""
    missing_value: str = "<null>"
    expanded: bool = False
    max_width: Option[U32] = _dataclasses.field(default_factory=lambda: _cott_default_OutputSettings_max_width)
    header_casing: Option[Opaque[Literal["pgcli.completion-catalog"]]] = _dataclasses.field(default_factory=lambda: _cott_default_OutputSettings_header_casing)
    style: Option[OutputStyle] = _dataclasses.field(default_factory=lambda: _cott_default_OutputSettings_style)
    tuples_only: bool = False
    query: str = ""

    def __post_init__(self) -> None:
        if not _cott_validated_construction():
            object.__setattr__(self, "table_format", _cott_validate_abi(self.table_format, str, path="$.table_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "column_date_formats", _cott_validate_abi(self.column_date_formats, FrozenMap[str, str], path="$.column_date_formats"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_field_width", _cott_validate_abi(self.max_field_width, Option[U32], path="$.max_field_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "decimal_format", _cott_validate_abi(self.decimal_format, str, path="$.decimal_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "float_format", _cott_validate_abi(self.float_format, str, path="$.float_format"))
        if not _cott_validated_construction():
            object.__setattr__(self, "missing_value", _cott_validate_abi(self.missing_value, str, path="$.missing_value"))
        if not _cott_validated_construction():
            object.__setattr__(self, "expanded", _cott_validate_abi(self.expanded, bool, path="$.expanded"))
        if not _cott_validated_construction():
            object.__setattr__(self, "max_width", _cott_validate_abi(self.max_width, Option[U32], path="$.max_width"))
        if not _cott_validated_construction():
            object.__setattr__(self, "header_casing", _cott_validate_abi(self.header_casing, Option[Opaque[Literal["pgcli.completion-catalog"]]], path="$.header_casing"))
        if not _cott_validated_construction():
            object.__setattr__(self, "style", _cott_validate_abi(self.style, Option[OutputStyle], path="$.style"))
        if not _cott_validated_construction():
            object.__setattr__(self, "tuples_only", _cott_validate_abi(self.tuples_only, bool, path="$.tuples_only"))
        if not _cott_validated_construction():
            object.__setattr__(self, "query", _cott_validate_abi(self.query, str, path="$.query"))

"""Why formatting a result failed. message is str() of the exception upstream pgcli raised
while formatting; the REPL prints it in red on stderr and discards every output item of
the command (an empty message prints an empty line)."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class OutputError_Failed:
    __hash__ = None
    message: str

OutputError: TypeAlias = Union[OutputError_Failed]

"""JSON object text mapping EXPLAIN plan node types to the description line pgcli's explain
visualizer prints under each node (pgcli/pyev.py DESCRIPTIONS, verbatim)."""
EXPLAIN_NODE_DESCRIPTIONS: Final[str] = "{\"Append\": \"Used in a UNION to merge multiple record sets by appending them together.\", \"Limit\": \"Returns a specified number of rows from a record set.\", \"Sort\": \"Sorts a record set based on the specified sort key.\", \"Nested Loop\": \"Merges two record sets by looping through every record in the first set and trying to find a match in the second set. All matching records are returned.\", \"Merge Join\": \"Merges two record sets by first sorting them on a join key.\", \"Hash\": \"Generates a hash table from the records in the input recordset. Hash is used by Hash Join.\", \"Hash Join\": \"Joins to record sets by hashing one of them (using a Hash Scan).\", \"Aggregate\": \"Groups records together based on a GROUP BY or aggregate function (e.g. sum()).\", \"Hashaggregate\": \"Groups records together based on a GROUP BY or aggregate function (e.g. sum()). Hash Aggregate uses a hash to first organize the records by a key.\", \"Sequence Scan\": \"Finds relevant records by sequentially scanning the input record set. When reading from a table, Seq Scans (unlike Index Scans) perform a single read operation (only the table is read).\", \"Seq Scan\": \"Finds relevant records by sequentially scanning the input record set. When reading from a table, Seq Scans (unlike Index Scans) perform a single read operation (only the table is read).\", \"Index Scan\": \"Finds relevant records based on an Index. Index Scans perform 2 read operations: one to read the index and another to read the actual value from the table.\", \"Index Only Scan\": \"Finds relevant records based on an Index. Index Only Scans perform a single read operation from the index and do not read from the corresponding table.\", \"Bitmap Heap Scan\": \"Searches through the pages returned by the Bitmap Index Scan for relevant rows.\", \"Bitmap Index Scan\": \"Uses a Bitmap Index (index which uses 1 bit per page) to find all relevant pages. Results of this node are fed to the Bitmap Heap Scan.\", \"CTEScan\": \"Performs a sequential scan of Common Table Expression (CTE) query results. Note that results of a CTE are materialized (calculated and temporarily stored).\", \"ProjectSet\": \"ProjectSet appears when the SELECT or ORDER BY clause of the query.  They basically just execute the set-returning function(s) for each tuple until none of the functions return any more records.\", \"Result\": \"Returns result\"}"

"""Build the Python row list of a ResultRows from Cell rows: a list with one tuple per row,
each cell converted as Null -> None, Text -> str, Integer -> int, Float -> float, Decimal
-> decimal.Decimal(value), Boolean -> bool, Array -> list of the converted items
(recursive), Other -> str."""
"""Format one statement result exactly like pgcli 4.7.1 main.format_output with the
lock-selected cli_helpers 2.15.1, tabulate 0.10.0, pygments and click. The output items
below are produced in order and returned as FormattedOutput(text="\\n".join(items),
items=len(items)). Any exception raised while producing the items, by the steps below or
by the library functions they call, yields Err(OutputError.Failed(message:
str(exception))) and no output.

1. Format name and validation. The format name is "plain" when settings.tuples_only,
else "vertical" when settings.expanded, else settings.table_format. expanded_view is
settings.expanded or settings.table_format == "vertical". When not explain_mode, a
non-empty format name that is not in table_format_names() fails before anything else,
even without a result, with message 'unrecognized format_name "<name>"' (an empty name
fails only when a table is rendered, with 'unrecognized format "None"').

2. Items. First the title when title is Some, non-empty and not tuples_only. Then the
table section (3) when result_set is Some and (rowcount >= 0 or rows is non-empty): a
cursor result prints its header even with zero rows, an empty list result prints nothing.
Last the footer when status is Some, non-empty and not tuples_only: status + " " +
str(rowcount) when result_set is Some, its rowcount >= 0, settings.max_width is Nothing
and status does not end with str(rowcount) (so "SHOW" becomes "SHOW 1"), otherwise
status unchanged.

3. Table section. headers is [] when tuples_only, else result_set.columns each mapped
through real.pgcli.completion.apply_identifier_casing(catalog, name) when
settings.header_casing is Some(catalog), unchanged when Nothing. The Python rows are the
Python list wrapped by result_set.rows (one tuple of Python values per row), used as is
and never mutated. When explain_mode the section is (6). Otherwise render
(4) with the format name; if that yields no item fail with message "" (upstream's
StopIteration). When not expanded_view, settings.max_width is Some(w) with w > 0, headers
is non-empty and len(cli_helpers.utils.strip_ansi(first item)) > w (code points), the
section is every item of rendering "vertical" (4) from the same Python rows and headers
(possibly none); otherwise it is every item of the first rendering.

4. Rendering a format F from Python rows and headers; this is cli_helpers
TabularOutputFormatter.format_output spelled out step by step, because the style cannot
be handed to cli_helpers without defining a pygments Style class.
(a) Column types, computed from the Python rows before any step (zero rows give []): per
column the highest rank of its values, None 0, int 2 (type(v) is int, bool excluded),
float or decimal.Decimal 3, bytes 4, anything else (str, bool, list) 5; rank 0 -> type(None),
2 -> int, 3 -> decimal.Decimal, 4 -> bytes, 5 -> str. Rank 3 maps to decimal.Decimal and
never to float (cli_helpers' inverse type table), which is exactly
TabularOutputFormatter()._get_column_types(rows).
(b) pgcli steps, each called as step(data, headers, column_types=types, **K) returning
(data, headers), with K = {"sep_title": "RECORD {n}", "sep_character": "-", "sep_length":
(1, 25), "missing_value": settings.missing_value, "integer_format":
settings.decimal_format, "float_format": settings.float_format, "column_date_formats":
dict of settings.column_date_formats, "disable_numparse": True, "preserve_whitespace":
True, "max_field_width": the max_field_width value or None}. When float_format is "",
cli_helpers.tabular_output.preprocessors.align_decimals (it changes nothing because no
column type is float; lists stay Python lists and print as reprs such as "[1, None]").
Otherwise preprocessors.format_numbers (it formats int values of int-typed columns with
format(v, decimal_format) when decimal_format is non-empty; float_format never applies
since no column type is float), then the array step: every row becomes
[format_array(v) if v is a list else v for v in row], where
format_array(None) = settings.missing_value, a non-list value stays itself and a list
becomes "{" + ",".join(str(format_array(e)) for e in items) + "}". Then, when
column_date_formats is non-empty, preprocessors.format_timestamps (a value whose column
header headers[i] is a key becomes datetime.fromisoformat(v).strftime(format); values
that fail stay; with tuples_only's empty headers any row raises IndexError "list index
out of range").
(c) The format's own steps and adapter, from cli_helpers.tabular_output, with data
passed as list(data) to the adapter:
- "vertical": null step, preprocessors.convert_to_string, header and row styling, then
  vertical_table_adapter.adapter(data, headers, sep_title="RECORD {n}", sep_character="-",
  sep_length=(1, 25)): one item per row, "-[ RECORD n ]-------------------------\\n"
  followed by "header.ljust(longest header length) | value" lines joined by "\\n".
- "csv", "csv-tab", "csv-noheader", "csv-tab-noheader": null step,
  preprocessors.bytes_to_string, then delimited_output_adapter.adapter(data, headers,
  table_format=F), passing dialect="unix" only when F is exactly "csv" (every field
  quoted); the other three keep the csv module's default excel dialect (a field is quoted
  only when it contains the delimiter, a quote or a line break); quotes are doubled, there
  is no line terminator, and a header item comes first unless the name contains
  "noheader".
- "tsv", "tsv_noheader": null step, bytes_to_string, convert_to_string, then
  tsv_output_adapter.adapter(data, headers, table_format=F).
- "jsonl", "jsonl_escaped": bytes_to_string, then json_output_adapter.adapter(data,
  headers, table_format=F).
- "sql-insert", "sql-update", "sql-update-1", "sql-update-2": (5).
- every other name (the tabulate formats): null step, convert_to_string,
  preprocessors.truncate_string(data, headers, max_field_width=K["max_field_width"]),
  header and row styling, preprocessors.escape_newlines unless
  tabulate.multiline_formats.get(F) is truthy (cli_helpers.tabular_output registers its
  extra formats there on import), then separator styling around
  tabulate_adapter.adapter(data, headers, table_format=F, preserve_whitespace=True,
  disable_numparse=True); one item per line.
Null step: every value that is None becomes style_text(settings.missing_value,
style.null, style.base, style.true_color) when settings.style is Some(style), else
settings.missing_value (csv and tsv included). Header and row styling, only when
settings.style is Some(style): when style.header != "" every header h becomes
style_text(h, style.header, style.base, style.true_color); when style.odd_row or
style.even_row is non-empty every field of the i-th row (i counted from 1) becomes
style_text(field, style.odd_row when i is odd else style.even_row, style.base,
style.true_color). Separator styling, only when settings.style is Some(style) and F is in
tabulate_adapter.supported_table_formats: for the duration of the adapter call
tabulate._table_formats[F] is replaced by a tabulate.TableFormat whose fields of exact
class tabulate.Line or tabulate.DataRow have each element s replaced by style_text(s,
style.table_separator, style.base, style.true_color), other fields kept; restore the
original entry afterwards (try/finally).

5. sql formats (pgcli packages/formatter/sqlformatter.py), with no own steps: values are
the Python values after (b) with None kept. Table name: when
real.pgcli.parseutils.extract_tables(settings.query) is non-empty and its first entry t
has t.schema = Some(s) with s non-empty, s + "." + t.name; with no or empty schema,
t.name; with no entry, "DUAL". Literal of a value v: None -> "NULL", bytes -> "X'" +
v.hex() + "'", anything else -> "'" + str(v) + "'" (no escaping). "sql-insert" items:
'INSERT INTO "<table>" ("' + '", "'.join(headers) + '") VALUES', then per row prefix +
"(" + ", ".join(literals) + ")" with prefix "  " for the first row and ", " after, then
";". "sql-update" (keys 1), "sql-update-1" (keys 1), "sql-update-2" (keys 2), per row:
'UPDATE "<table>" SET', then for each column i from keys on prefix + '"' + headers[i] +
'" = ' + literal(row[i]) with prefix "  " for the first and ", " after, then "WHERE " +
" AND ".join('"' + headers[i] + '" = ' + literal(row[i]) for i in range(keys)) + ";"
(headers[i] beyond the columns raises IndexError "list index out of range"). Write the
adapter as a top-level private generator function adapter(data, headers,
table_format, query) that receives the query as an argument.

6. Explain mode. The Python rows are unpacked as in Python's [(value,)] = rows, which
accepts exactly one row holding exactly one value: zero rows or a row without values fail
"not enough values to unpack (expected 1, got 0)", n > 1 rows or values fail "too many
values to unpack (expected 1, got n)". A value that is not a str fails with str() of the
TypeError that json.loads(value) raises for it (its text ends with the offending type
name, e.g. "..., not int"). The section is the items
of visualize_explain_plans(value, w) with w = the max_width value when it is Some and
non-zero, else 100 (its text holds its items joined by "\\n"; its error is returned as
is); zero items fails with message "". There is no auto-vertical fallback in explain
mode."""
"""Wrap text in the ANSI SGR sequences pygments 2.21 emits for a token whose style
definition is `definition` and whose root Token style is `base`, the way cli_helpers
utils.style_field does with pgcli's output style class: Terminal256Formatter when
true_color is false, TerminalTrueColorFormatter when it is true.

Attributes start as color "", bgcolor "", bold, italic and underline false; apply the
whitespace-separated words of base, then those of definition, left to right: "bold",
"italic", "underline" set their flag and "nobold", "noitalic", "nounderline" clear it;
"bg:X" sets bgcolor to colorformat(X); "noinherit", "roman", "sans", "mono" and
"border:X" change nothing; any other word sets color to colorformat(word).
colorformat(X) is X when X is one of the 16 pygments ANSI color names
(pygments.style.ansicolors: ansiblack, ansired, ansigreen, ansiyellow, ansiblue,
ansimagenta, ansicyan, ansigray, ansibrightblack, ansibrightred, ansibrightgreen,
ansibrightyellow, ansibrightblue, ansibrightmagenta, ansibrightcyan, ansiwhite); the 6
characters after "#" when X is "#" plus 6 characters; the 3 characters after "#" each
doubled when X is "#" plus 3 characters ("#eee" -> "eeeeee"); X unchanged for
"transparent" and words starting with "var" or "calc"; any other word is ignored
(pygments rejects such a style when pgcli builds it).

Sequences: construct pygments.formatters.terminal256.EscapeSequence(fg=fg, bg=bg,
bold=bold, underline=underline, italic=italic). 256 colors: fg is the ANSI name itself
when color is an ANSI name, Terminal256Formatter()._color_index(color) (the nearest
xterm-256 index, 0 for a non-hex value) when color is another non-empty value, else
None; bg likewise from bgcolor; on = color_string(), off = reset_string(). True color:
an ANSI name is first replaced by its hex digits from pygments.style._ansimap (ansigreen
-> "007f00"); fg is TerminalTrueColorFormatter()._color_tuple(color) (None for a non-hex
value) when color is non-empty, else None; bg likewise; on = true_color_string(), off =
reset_string(). Examples (ESC written \\e): "#00ff5f bold" gives \\e[38;5;47;01m and
\\e[39;00m (true color \\e[38;2;0;255;95;01m), "#808080" gives \\e[38;5;244m and \\e[39m,
"bold ansibrightred" gives \\e[91;01m and \\e[39;00m, "bg:#eee #111" gives
\\e[38;5;233;48;5;255m and \\e[39;49m, "italic" gives \\e[03m and \\e[00m, empty attributes
give no sequences.

Result: text split on "\\n"; each non-empty piece becomes on + piece + off, empty pieces
stay empty, and the pieces are joined again with "\\n"."""
"""Render EXPLAIN (ANALYZE, COSTS, VERBOSE, BUFFERS, FORMAT JSON) output the way pgcli's
explain visualizer does (pgcli/pyev.py Visualizer with color on, used by
explain_output_formatter.py). Any exception (invalid JSON, a missing key, a division by
zero, textwrap's invalid width) yields Err(OutputError.Failed(message: str(exception))),
e.g. a missing key gives the quoted key such as "'Execution Time'".

Decode plan_json with json.loads and iterate the decoded value (a list's elements; a
dict iterates its keys). The result is FormattedOutput(text="\\n".join(items),
items=len(items)). For each element E produce one item: plan = E.pop("Plan") and
explain = E (the rest of E); process the plan, mark outliers, generate the lines and
join them with "\\n". Node values are read as node["Key"] where the text says so (a
missing key raises KeyError) and with .get where it says "if present".

Colors come from click.style: bb(s) = click.style(s, fg="bright_black"), white(s) =
click.style(s, fg="white"), tag(s) = click.style(s, fg="white", bg="red"), green,
yellow, red and cyan likewise with that fg (click.style styles "" too, giving
"\\x1b[90m\\x1b[0m").

Processing, pre-order (a node before its children, children in order), per node N:
estimate: factor = 0, direction = "Under"; unless N["Plan Rows"] == N["Actual Rows"]: if
Plan Rows != 0, factor = Actual Rows / Plan Rows; then if factor < 10: factor = 0,
direction = "Over", and if Actual Rows != 0, factor = Plan Rows / Actual Rows. Actuals:
duration = N["Actual Total Time"], cost = N["Total Cost"]; for each child C in
N.get("Plans", []) whose C["Node Type"] != "CTEScan": duration -= C["Actual Total Time"],
cost -= C["Total Cost"] (the children's raw values); cost = 0 if cost < 0; duration =
duration * N["Actual Loops"]. Maximums: for (key, value) in ("Max Rows", Actual Rows),
("Max Cost", cost), ("Max Duration", duration), ("Total Cost", cost): explain[key] =
value when explain.get(key) is missing or falsy, or when explain[key] < value. After all
nodes: outliers per node, costliest = cost == explain["Max Cost"], largest = Actual Rows
== explain["Max Rows"], slowest = duration == explain["Max Duration"].

Formatting helpers. dur(v): v < 1 -> green("<1 ms"); v < 100 -> green("%.2f ms" % v); v <
1000 -> yellow("%.2f ms" % v); v < 60000 -> red("%.2f s" % (v / 1000.0)); else red("%.2f
m" % (v / 60000.0)). intcomma(v): int(v) unless v is a str, then str, then insert ","
thousands separators by repeating re.sub(r"^(-?\\d+)(\\d{3})", r"\\g<1>,\\g<2>", s) until it
stops changing ("123448.48" as a number -> "123,448"). wrap(text, cols) is [text] when
cols == 0, else textwrap.wrap(text, cols). desc(type) is the entry for the node type in
EXPLAIN_NODE_DESCRIPTIONS (a JSON object) or "Not found : " + type.

Lines: "○ Total Cost: " + intcomma(explain["Total Cost"]), "○ Planning Time: " +
dur(explain["Planning Time"]), "○ Execution Time: " + dur(explain["Execution Time"]),
bb("┬"), then node_lines(plan, prefix "", width terminal_width, last = the root has
exactly one child in "Plans").

node_lines(N, prefix, width, last), where out(p, s) appends bb(p) + s:
out(prefix, bb("│")); out(prefix, bb(("└" if last else "├") + "─⌠") + " " +
white(N["Node Type"]) + details + " " + tags), where details = bb(" [" + ", ".join(parts) +
"]") for the truthy values among N.get("Scan Direction") and N.get("Strategy") in that
order ("" when none) and tags = " ".join of tag("slowest") if slowest, tag("costliest") if
costliest, tag("largest") if largest, tag("bad estimate") if factor >= 100 (so a node
without tags keeps a trailing space). Then prefix2 = prefix + ("  " if last else "│ "),
p = prefix2 + "│ ", cols = width - len(p). For each line of wrap(desc(N["Node Type"]),
cols): out(p, bb(line)). If duration is truthy: out(p, "○ Duration: " + dur(duration) +
" (%.0f%%)" % (duration / explain["Execution Time"] * 100)). out(p, "○ Cost: " +
intcomma(cost) + " (%.0f%%)" % (cost / explain["Total Cost"] * 100)). out(p, "○ Rows: "
+ intcomma(N["Actual Rows"])). Then with q = p + "  ", each if present and truthy, in this
order: "Join Type" -> out(q, join_type + " " + bb("join")); "Relation Name" -> out(q,
bb("on") + " " + str(N.get("Schema", "unknown")) + "." + relation); "Index Name" ->
out(q, bb("using") + " " + index); "Index Condition" -> out(q, bb("condition") + " " +
condition); "Filter" -> out(q, bb("filter") + " " + filter + " " + bb("[-" +
intcomma(N["Rows Removed by Filter"]) + " rows]")); "Hash Condition" -> out(q, bb("on") +
" " + condition); "CTE Name" -> out(q, "CTE " + name). If factor != 0: out(q, bb("rows")
+ " " + direction + "estimated " + bb("by") + " " + "%.2f" % factor + "x"). If
N.get("Output", []) is non-empty: for index, line in enumerate(wrap(" + ".join(outputs),
cols)): out(prefix2, bb(terminator) + cyan(line)) where terminator is, for index 0, "⌡► "
when N has no children and "├►  " otherwise, for later indexes "   " without children and
"│  " with children. Finally node_lines(child, prefix2, width, last = it is the last
child) for each child in order. Values are inserted with str() ("%s")."""
"""The table format names pgcli accepts, in the order \\T lists them:
TabularOutputFormatter().supported_formats of cli_helpers 2.15.1 after pgcli registered
its four sql formats. Exactly: vertical, csv, csv-tab, csv-noheader, csv-tab-noheader,
mediawiki, html, latex, latex_booktabs, textile, moinmoin, jira, ascii, ascii_escaped,
plain, simple, minimal, grid, fancy_grid, pipe, orgtbl, psql, psql_unicode, rst, github,
double, mysql, mysql_unicode, mysql_heavy, tsv, tsv_noheader, jsonl, jsonl_escaped,
sql-insert, sql-update, sql-update-1, sql-update-2."""
"""pgcli main.duration_in_words. When seconds is 0 the result is "0 seconds". Otherwise
hours, rest = divmod(seconds, 3600) and minutes, secs = divmod(rest, 60) (Python float
divmod); the parts, joined by " ", are: f"{int(hours)} hours" when hours > 1, "1 hour"
when hours == 1; f"{int(minutes)} minutes" when minutes > 1, "1 minute" when minutes ==
1; f"{int(secs)} seconds" when secs >= 2, "1 second" when secs >= 1, otherwise when secs
is non-zero f"{round(secs, 3)} second" (0.2 -> "0.2 second", 0.0004 -> "0.0 second")."""
"""The timing line pgcli prints after a command when \\timing is on. When total_seconds > 1:
"Time: %0.03fs (%s), executed in: %0.03fs (%s)" % (total_seconds,
duration_in_words(total_seconds), execution_seconds,
duration_in_words(execution_seconds)); otherwise "Time: %0.03fs" % total_seconds."""
__all__ = ["Cell", "Cell_Array", "Cell_Boolean", "Cell_Decimal", "Cell_Float", "Cell_Integer", "Cell_Null", "Cell_Other", "Cell_Text", "EXPLAIN_NODE_DESCRIPTIONS", "FormattedOutput", "OutputError", "OutputError_Failed", "OutputSettings", "OutputStyle", "ResultRows", "ResultSet"]
