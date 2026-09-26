import fnmatch
import os
import pathlib
import tempfile
import threading
import time
from datetime import datetime, timezone
from typing import Any, Final, cast

import pyarrow
from cott_runtime import U64, CottList, Nothing, Ok, Opaque, Some

from real.harlequin.adapters import cancel_queries, execute_statements, fetch_result, load_catalog, load_catalog_children, search_catalog
from real.harlequin.adapters_types import Connection
from real.harlequin.catalog import catalog_children, normalize_catalog, replace_children
from real.harlequin.catalog_types import CatalogEntry, CatalogKind, CatalogKind_Bucket, CatalogKind_Column, CatalogKind_Database, CatalogKind_Directory, CatalogKind_File, CatalogKind_Object, CatalogKind_Prefix, CatalogKind_Schema, CatalogKind_Table, CatalogKind_TemporaryTable, CatalogKind_View
from real.harlequin.export import write_result
from real.harlequin.export_types import ExportError_InvalidOption, ExportError_PathIsDirectory, ExportError_UnknownFormat, ExportOptionValue, ExportRequest
from real.harlequin.history import record_query, update_query
from real.harlequin.history_types import QueryRecord, QueryStatus, QueryStatus_Canceled, QueryStatus_Error, QueryStatus_Ok
from real.harlequin.hsql import hsql_error_line, layout_text, missing_label_message, parse_catalog_path, spell_catalog_label, stats_json
from real.harlequin.hsql_types import HsqlArguments, HsqlContext, HsqlError, HsqlError_Connection, HsqlError_Crash, HsqlError_Interrupted, HsqlError_Query, HsqlError_Timeout, HsqlError_Usage, HsqlMode_Catalog, HsqlMode_CatalogSearch, HsqlMode_Execute, HsqlResponse, LayoutOptions, SqlSource_Command
from real.harlequin.results_types import ColumnInfo, ResultSet
from real.harlequin.sqltext import redact_sql, redact_text, split_statements

_CANCELED_TITLE: Final[str] = "Query canceled"


def _status_of(error: HsqlError) -> int:
    if isinstance(error, HsqlError_Usage):
        return 2
    if isinstance(error, HsqlError_Query):
        return 1
    if isinstance(error, HsqlError_Connection):
        return 3
    if isinstance(error, HsqlError_Timeout):
        return 4
    if isinstance(error, HsqlError_Interrupted):
        return 130
    return 70


def _fail(error: HsqlError) -> tuple[bytes, str, int]:
    return b"", hsql_error_line(error), _status_of(error)


def _fire_timeout(cells: dict[str, bool], connection: Connection) -> None:
    cells["timed_out"] = True
    cancel_queries(connection)


def _resolve(cwd: pathlib.Path, path: str) -> pathlib.Path:
    target = pathlib.Path(path).expanduser()
    if target.is_absolute():
        return target
    return cwd / target


def _os_reason(error: OSError) -> str:
    return error.strerror if error.strerror else str(error)


def _read_sources(arguments: HsqlArguments, cwd: pathlib.Path, stdin_text: Some[str] | Nothing) -> list[str] | HsqlError:
    statements: list[str] = []
    for source in arguments.sources:
        if isinstance(source, SqlSource_Command):
            text = source.sql
        elif source.path == "-":
            text = stdin_text.value if isinstance(stdin_text, Some) else ""
        else:
            try:
                text = _resolve(cwd, source.path).read_text(encoding="utf-8")
            except OSError as error:
                return HsqlError_Usage(message=f"could not read {source.path}: {_os_reason(error)}")
            except UnicodeDecodeError as error:
                return HsqlError_Usage(message=f"could not read {source.path}: {error}")
        statements.extend(split_statements(text))
    return statements


def _statement_error(cells: dict[str, bool], timeout: Some[float] | Nothing, title: str, message: str) -> HsqlError:
    if cells["timed_out"] and isinstance(timeout, Some):
        return HsqlError_Timeout(message=f"timed out after {timeout.value:g}s")
    return HsqlError_Query(message=f"{title}\n{message}")


def _begin_log(connection: Connection, context: HsqlContext, sql: str) -> int | None:
    run_at = datetime.now(timezone.utc).isoformat()
    record = QueryRecord(run_at=run_at, program="hsql", connection=connection.connection_id, profile=context.profile, adapter=context.adapter_name, sql=redact_sql(sql, context.secrets), status=QueryStatus_Ok(), rows=Nothing(), truncated=Nothing(), elapsed_ms=Nothing(), error_text=Nothing())
    recorded = record_query(context.query_log, record)
    return recorded.value if isinstance(recorded, Ok) else None


def _log(context: HsqlContext, row: int | None, status: QueryStatus, rows: Some[int] | Nothing, truncated: Some[bool] | Nothing, elapsed_ms: Some[float] | Nothing, error_text: Some[str] | Nothing) -> None:
    if row is not None:
        redacted: Some[str] | Nothing = Some(value=redact_text(error_text.value, context.secrets)) if isinstance(error_text, Some) else Nothing()
        update_query(context.query_log, row, status, rows, truncated, elapsed_ms, redacted)


def _select(results: list[ResultSet], choice: str) -> tuple[list[ResultSet], HsqlError | None]:
    if choice == "all":
        return results, None
    if choice == "last":
        return results[-1:], None
    try:
        number = int(choice)
    except ValueError:
        return [], HsqlError_Usage(message=f"--result must be all, last or a number, not {choice}")
    if number < 1 or number > len(results):
        return [], HsqlError_Usage(message=f"--result {choice} is out of range: the run produced {len(results)} result sets")
    return [results[number - 1]], None


def _write_file(path: pathlib.Path, data: bytes) -> HsqlError | None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    except OSError as error:
        return HsqlError_Usage(message=f"could not write {path}: {_os_reason(error)}")
    return None


def _render_layout(result_set: ResultSet, fmt: str, arguments: HsqlArguments, context: HsqlContext, to_file: bool) -> tuple[str, str]:
    display = arguments.display_rows
    max_rows: Some[U64] | Nothing
    if isinstance(display, Some):
        max_rows = Nothing() if display.value < 0 else Some(value=display.value)
    else:
        max_rows = Some(value=10 if fmt == "vertical" else 40)
    if arguments.color == "always":
        color = True
    elif arguments.color == "auto":
        color = context.stdout_tty and not context.no_color and not to_file
    else:
        color = False
    footer = not (arguments.tuples_only or arguments.no_footer)
    options = LayoutOptions(header=not (arguments.tuples_only or arguments.no_header), footer=footer, aligned=not arguments.no_align, null_string=arguments.null_string, color=color, max_rows=max_rows)
    text = layout_text(result_set, fmt, options)
    note = ""
    total = result_set.fetched_row_count
    if not footer and isinstance(max_rows, Some) and total > max_rows.value:
        note = f"note: printed {max_rows.value} of {total} rows; pass --display-rows -1 for all of them\n"
    return text, note


def _suffix(fmt: str) -> str:
    if fmt in ("table", "vertical"):
        return ".txt"
    if fmt in ("markdown", "md"):
        return ".md"
    return "." + fmt


def _export(result_set: ResultSet, fmt: str, arguments: HsqlArguments) -> bytes | HsqlError:
    options: list[ExportOptionValue] = []
    if fmt in ("csv", "tsv"):
        null = arguments.null_string
        options.append(ExportOptionValue(name="na_rep", value=null.value if isinstance(null, Some) else ""))
        if arguments.tuples_only or arguments.no_header:
            options.append(ExportOptionValue(name="header", value="false"))
    if fmt == "json":
        options.append(ExportOptionValue(name="array", value="true"))
    with tempfile.TemporaryDirectory() as folder:
        path = pathlib.Path(folder) / ("result" + _suffix(fmt))
        written = write_result(result_set, ExportRequest(path=path, format=fmt, options=CottList(values=options)))
        if isinstance(written, Ok):
            try:
                return path.read_bytes()
            except OSError as error:
                return HsqlError_Query(message=f"could not read the exported file: {_os_reason(error)}")
        error = written.error
        if isinstance(error, ExportError_UnknownFormat):
            return HsqlError_Usage(message=f"unknown format {error.name}")
        if isinstance(error, ExportError_InvalidOption):
            return HsqlError_Usage(message=f"invalid {error.name} option: {error.message}")
        if isinstance(error, ExportError_PathIsDirectory):
            return HsqlError_Query(message=f"{error.path} is a directory")
        return HsqlError_Query(message=f"{error.title}\n{error.message}")


def _emit(results: list[ResultSet], arguments: HsqlArguments, cwd: pathlib.Path, context: HsqlContext) -> tuple[bytes, list[str], HsqlError | None]:
    fmt = arguments.format
    notes: list[str] = []
    layouts = ("table", "markdown", "md", "vertical")
    single = ("csv", "tsv", "json", "parquet", "orc", "feather", "arrow")
    selected, selection_error = _select(results, arguments.result)
    if selection_error is not None:
        return b"", notes, selection_error
    out_dir: pathlib.Path | None = None
    out_file: pathlib.Path | None = None
    output = arguments.output
    if isinstance(output, Some):
        target = _resolve(cwd, output.value)
        if target.is_dir() or output.value.endswith(("/", os.sep)):
            out_dir = target
        else:
            out_file = target
    if fmt not in layouts and isinstance(arguments.display_rows, Some):
        notes.append("note: --display-rows only applies to text layouts; use --limit to fetch fewer rows.\n")
    if fmt in single and len(selected) > 1 and out_dir is None:
        return b"", notes, HsqlError_Usage(message=f"{len(selected)} result sets, but {fmt} holds one; use --result last, --result N, or -o DIR for one file each")
    if fmt == "none":
        return b"", notes, None
    chunks: list[bytes] = []
    truncated = False
    for index, result_set in enumerate(selected, 1):
        truncated = truncated or result_set.truncated
        if fmt in layouts:
            text, note = _render_layout(result_set, fmt, arguments, context, out_dir is not None or out_file is not None)
            if note:
                notes.append(note)
            data = text.encode("utf-8")
        else:
            exported = _export(result_set, fmt, arguments)
            if not isinstance(exported, bytes):
                return (b"".join(chunks) if out_file is None else b""), notes, exported
            data = exported
        if out_dir is not None:
            path = out_dir / f"result-{index}{_suffix(fmt)}"
            failure = _write_file(path, data)
            if failure is not None:
                return b"", notes, failure
            notes.append(f"note: wrote {path}\n")
        else:
            chunks.append(data)
    if truncated:
        notes.append(f"note: results truncated at --limit {arguments.limit}; pass --limit -1 for all rows\n")
    body = b"\n".join(chunks) if fmt in layouts else b"".join(chunks)
    if out_file is not None:
        failure = _write_file(out_file, body)
        return b"", notes, failure
    return body, notes, None


def _run_execute(connection: Connection, arguments: HsqlArguments, cwd: pathlib.Path, stdin_text: Some[str] | Nothing, context: HsqlContext) -> tuple[bytes, str, int]:
    read = _read_sources(arguments, cwd, stdin_text)
    if not isinstance(read, list):
        return _fail(read)
    statements = read
    limit: Some[U64] | Nothing = Some(value=arguments.limit) if arguments.limit >= 0 else Nothing()
    cells: dict[str, bool] = {"timed_out": False}
    timeout = arguments.timeout_seconds
    timer: threading.Timer | None = None
    if isinstance(timeout, Some):
        timer = threading.Timer(timeout.value, lambda: _fire_timeout(cells, connection))
        timer.daemon = True
        timer.start()
    started = time.monotonic()
    results: list[ResultSet] = []
    errors: list[HsqlError] = []
    try:
        executed_list = execute_statements(connection, CottList(values=statements), limit, arguments.continue_on_error)
        for executed in executed_list:
            row = _begin_log(connection, context, executed.sql) if arguments.write_history else None
            failure = executed.failure
            problem_title: str | None = None
            problem_message = ""
            if isinstance(failure, Some):
                problem_title = failure.value.title
                problem_message = failure.value.message
            elif isinstance(executed.cursor, Some):
                fetched = fetch_result(connection, executed, limit, Nothing())
                if isinstance(fetched, Ok):
                    result_set = fetched.value
                    results.append(result_set)
                    _log(context, row, QueryStatus_Ok(), Some(value=result_set.fetched_row_count), Some(value=result_set.truncated), Some(value=round(float(result_set.elapsed_ms), 3)), Nothing())
                else:
                    problem_title = fetched.error.title
                    problem_message = fetched.error.message
            else:
                _log(context, row, QueryStatus_Ok(), Nothing(), Nothing(), Nothing(), Nothing())
            if problem_title is not None:
                errors.append(_statement_error(cells, timeout, problem_title, problem_message))
                status: QueryStatus = QueryStatus_Canceled() if problem_title == _CANCELED_TITLE or cells["timed_out"] else QueryStatus_Error()
                _log(context, row, status, Nothing(), Nothing(), Nothing(), Some(value=f"{problem_title}\n{problem_message}"))
    finally:
        if timer is not None:
            timer.cancel()
    if cells["timed_out"] and isinstance(timeout, Some) and not errors:
        errors.append(HsqlError_Timeout(message=f"timed out after {timeout.value:g}s"))
    elapsed = int((time.monotonic() - started) * 1000)
    stdout, notes, write_error = _emit(results, arguments, cwd, context)
    stderr = "".join(notes)
    status_code = 0
    first_failure: HsqlError | None = None
    for error in errors:
        stderr += hsql_error_line(error)
        if first_failure is None:
            first_failure = error
            status_code = _status_of(error)
    if write_error is not None:
        stderr += hsql_error_line(write_error)
        if first_failure is None:
            first_failure = write_error
            status_code = _status_of(write_error)
    if arguments.stats:
        label = "ok" if status_code == 0 else ("timeout" if status_code == 4 else "error")
        columns: CottList[ColumnInfo] = results[-1].columns if results else CottList(values=[])
        failure_text: Some[str] | Nothing = Nothing()
        if first_failure is not None:
            failure_text = Some(value=hsql_error_line(first_failure).removeprefix("hsql: error: ").rstrip("\n"))
        stderr += stats_json(label, len(statements), sum(result.fetched_row_count for result in results), any(result.truncated for result in results), limit, elapsed, columns, failure_text)
    return stdout, stderr, status_code


def _kind_name(kind: CatalogKind) -> str:
    if isinstance(kind, CatalogKind_Database):
        return "database"
    if isinstance(kind, CatalogKind_Schema):
        return "schema"
    if isinstance(kind, CatalogKind_Table):
        return "table"
    if isinstance(kind, CatalogKind_View):
        return "view"
    if isinstance(kind, CatalogKind_TemporaryTable):
        return "temporary table"
    if isinstance(kind, CatalogKind_Column):
        return "column"
    if isinstance(kind, CatalogKind_Directory):
        return "directory"
    if isinstance(kind, CatalogKind_File):
        return "file"
    if isinstance(kind, CatalogKind_Bucket):
        return "bucket"
    if isinstance(kind, CatalogKind_Prefix):
        return "prefix"
    if isinstance(kind, CatalogKind_Object):
        return "object"
    return "other"


def _catalog_result(rows: list[tuple[str, CatalogEntry]], elapsed_ms: int) -> ResultSet:
    pa: Any = pyarrow
    names = ["path", "name", "query_name", "type", "type_label"]
    values: list[list[str]] = [[path for path, _ in rows], [entry.label for _, entry in rows], [entry.query_name for _, entry in rows], [_kind_name(entry.kind) for _, entry in rows], [entry.type_label for _, entry in rows]]
    arrays = [pa.array(column, type=pa.string()) for column in values]
    table = cast(object, pa.table(arrays, names=names))
    count = len(rows)
    columns = CottList(values=[ColumnInfo(name=name, type_label="s") for name in names])
    return ResultSet(statement="", columns=columns, data=Opaque(tag="harlequin.arrow_table", value=table), row_count=count, fetched_row_count=count, truncated=False, elapsed_ms=elapsed_ms)


def _label_chain(entry: CatalogEntry, by_id: dict[str, CatalogEntry]) -> list[str]:
    labels: list[str] = [entry.label]
    current = entry
    while True:
        parent = current.parent
        if not isinstance(parent, Some) or parent.value not in by_id:
            break
        current = by_id[parent.value]
        labels.append(current.label)
    labels.reverse()
    return labels


def _run_catalog(connection: Connection, arguments: HsqlArguments, cwd: pathlib.Path, context: HsqlContext) -> tuple[bytes, str, int]:
    started = time.monotonic()
    raw_path = arguments.catalog_path
    parsed = parse_catalog_path(raw_path.value if isinstance(raw_path, Some) else "")
    if not isinstance(parsed, Ok):
        return _fail(parsed.error)
    scope = parsed.value
    segments = [segment for segment in scope.segments]
    pattern = scope.pattern
    rows: list[tuple[str, CatalogEntry]] = []
    mode = arguments.mode
    if isinstance(mode, HsqlMode_CatalogSearch):
        found = search_catalog(connection, mode.term)
        if not isinstance(found, Ok):
            return _fail(HsqlError_Query(message=f"{found.error.title}\n{found.error.message}"))
        entries = normalize_catalog(found.value)
        by_id: dict[str, CatalogEntry] = {entry.id: entry for entry in entries}
        depth = len(segments)
        for entry in entries:
            labels = _label_chain(entry, by_id)
            if len(labels) <= depth or labels[:depth] != segments:
                continue
            if isinstance(pattern, Some) and not fnmatch.fnmatchcase(labels[depth], pattern.value):
                continue
            rows.append((".".join(spell_catalog_label(label) for label in labels), entry))
    else:
        loaded = load_catalog(connection)
        if not isinstance(loaded, Ok):
            return _fail(HsqlError_Query(message=f"{loaded.error.title}\n{loaded.error.message}"))
        catalog = normalize_catalog(loaded.value)
        parent_id: str | None = None
        spelled: list[str] = []
        for segment in segments:
            kids = catalog_children(catalog, Some(value=parent_id) if parent_id is not None else Nothing())
            match: CatalogEntry | None = None
            for kid in kids:
                if kid.label == segment:
                    match = kid
                    break
            if match is None:
                parent_text: Some[str] | Nothing = Some(value=".".join(spelled)) if spelled else Nothing()
                return _fail(HsqlError_Usage(message=missing_label_message(segment, parent_text, CottList(values=[kid.label for kid in kids]))))
            spelled.append(spell_catalog_label(segment))
            parent_id = match.id
            if match.expandable and not match.loaded:
                children = load_catalog_children(connection, match)
                if not isinstance(children, Ok):
                    return _fail(HsqlError_Query(message=f"{children.error.title}\n{children.error.message}"))
                catalog = replace_children(catalog, match.id, children.value)
        listed = catalog_children(catalog, Some(value=parent_id) if parent_id is not None else Nothing())
        for entry in listed:
            if isinstance(pattern, Some) and not fnmatch.fnmatchcase(entry.label, pattern.value):
                continue
            rows.append((".".join([*spelled, spell_catalog_label(entry.label)]), entry))
    result_set = _catalog_result(rows, int((time.monotonic() - started) * 1000))
    stdout, notes, write_error = _emit([result_set], arguments, cwd, context)
    stderr = "".join(notes)
    if write_error is not None:
        return stdout, stderr + hsql_error_line(write_error), _status_of(write_error)
    return stdout, stderr, 0


def _serve(connection: Connection, arguments: HsqlArguments, cwd: pathlib.Path, stdin_text: Some[str] | Nothing, context: HsqlContext) -> tuple[bytes, str, int]:
    mode = arguments.mode
    if isinstance(mode, HsqlMode_Execute):
        return _run_execute(connection, arguments, cwd, stdin_text, context)
    if isinstance(mode, HsqlMode_Catalog) or isinstance(mode, HsqlMode_CatalogSearch):
        return _run_catalog(connection, arguments, cwd, context)
    return _fail(HsqlError_Usage(message="this mode does not run SQL on a connection"))


def execute_hsql_request(connection: Connection, arguments: HsqlArguments, cwd: pathlib.Path, stdin_text: Some[str] | Nothing, context: HsqlContext) -> HsqlResponse:
    try:
        stdout, stderr, status = _serve(connection, arguments, cwd, stdin_text, context)
    except KeyboardInterrupt:
        stdout, stderr, status = b"", hsql_error_line(HsqlError_Interrupted()), 130
    except Exception as error:
        stdout, stderr, status = b"", hsql_error_line(HsqlError_Crash(message=str(error))), 70
    return HsqlResponse(stdout=stdout, stderr=redact_text(stderr, context.secrets), status=status)
