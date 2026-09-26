from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.pgcli.output_types import Cell as Cell, Cell_Array as Cell_Array, Cell_Boolean as Cell_Boolean, Cell_Decimal as Cell_Decimal, Cell_Float as Cell_Float, Cell_Integer as Cell_Integer, Cell_Null as Cell_Null, Cell_Other as Cell_Other, Cell_Text as Cell_Text, EXPLAIN_NODE_DESCRIPTIONS as EXPLAIN_NODE_DESCRIPTIONS, FormattedOutput as FormattedOutput, OutputError as OutputError, OutputError_Failed as OutputError_Failed, OutputSettings as OutputSettings, OutputStyle as OutputStyle, ResultRows as ResultRows, ResultSet as ResultSet
"""Build the Python row list of a ResultRows from Cell rows: a list with one tuple per row,
each cell converted as Null -> None, Text -> str, Integer -> int, Float -> float, Decimal
-> decimal.Decimal(value), Boolean -> bool, Array -> list of the converted items
(recursive), Other -> str."""
def result_rows_from_cells(rows: CottList[CottList[Cell]]) -> Opaque[Literal["pgcli.result-rows"]]: ...

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
def format_output(title: Option[str], result_set: Option[ResultSet], status: Option[str], settings: OutputSettings, explain_mode: bool) -> Result[FormattedOutput, OutputError]: ...

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
def style_text(text: str, definition: str, base: str, true_color: bool) -> str: ...

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
def visualize_explain_plans(plan_json: str, terminal_width: U32) -> Result[FormattedOutput, OutputError]: ...

"""The table format names pgcli accepts, in the order \\T lists them:
TabularOutputFormatter().supported_formats of cli_helpers 2.15.1 after pgcli registered
its four sql formats. Exactly: vertical, csv, csv-tab, csv-noheader, csv-tab-noheader,
mediawiki, html, latex, latex_booktabs, textile, moinmoin, jira, ascii, ascii_escaped,
plain, simple, minimal, grid, fancy_grid, pipe, orgtbl, psql, psql_unicode, rst, github,
double, mysql, mysql_unicode, mysql_heavy, tsv, tsv_noheader, jsonl, jsonl_escaped,
sql-insert, sql-update, sql-update-1, sql-update-2."""
def table_format_names() -> CottList[str]: ...

"""pgcli main.duration_in_words. When seconds is 0 the result is "0 seconds". Otherwise
hours, rest = divmod(seconds, 3600) and minutes, secs = divmod(rest, 60) (Python float
divmod); the parts, joined by " ", are: f"{int(hours)} hours" when hours > 1, "1 hour"
when hours == 1; f"{int(minutes)} minutes" when minutes > 1, "1 minute" when minutes ==
1; f"{int(secs)} seconds" when secs >= 2, "1 second" when secs >= 1, otherwise when secs
is non-zero f"{round(secs, 3)} second" (0.2 -> "0.2 second", 0.0004 -> "0.0 second")."""
def duration_in_words(seconds: F64) -> str: ...

"""The timing line pgcli prints after a command when \\timing is on. When total_seconds > 1:
"Time: %0.03fs (%s), executed in: %0.03fs (%s)" % (total_seconds,
duration_in_words(total_seconds), execution_seconds,
duration_in_words(execution_seconds)); otherwise "Time: %0.03fs" % total_seconds."""
def timing_report(total_seconds: F64, execution_seconds: F64) -> str: ...

__all__ = ["Cell", "Cell_Array", "Cell_Boolean", "Cell_Decimal", "Cell_Float", "Cell_Integer", "Cell_Null", "Cell_Other", "Cell_Text", "EXPLAIN_NODE_DESCRIPTIONS", "FormattedOutput", "OutputError", "OutputError_Failed", "OutputSettings", "OutputStyle", "ResultRows", "ResultSet", "duration_in_words", "format_output", "result_rows_from_cells", "style_text", "table_format_names", "timing_report", "visualize_explain_plans"]
