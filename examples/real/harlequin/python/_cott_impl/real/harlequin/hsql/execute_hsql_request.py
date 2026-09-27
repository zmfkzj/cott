import fnmatch
import os
import pathlib
import tempfile
import threading
import time
from datetime import datetime, timezone
from typing import Any, cast

import pyarrow
from cott_runtime import CottList, I64, Nothing, Ok, Opaque, Some, U64
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


def _status(error: HsqlError) -> I64:
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


def _resolve(cwd: pathlib.Path, path: str) -> pathlib.Path:
    target = pathlib.Path(path).expanduser()
    return target if target.is_absolute() else cwd / target


def _reason(error: OSError) -> str:
    return error.strerror if error.strerror else str(error)


def _sources(arguments: HsqlArguments, cwd: pathlib.Path, stdin_text: Some[str] | Nothing) -> list[str] | HsqlError:
    statements: list[str] = []
    for source in arguments.sources:
        if isinstance(source, SqlSource_Command):
            text = source.sql
        elif source.path == "-":
            text = stdin_text.value if isinstance(stdin_text, Some) else ""
        else:
            try:
                text = _resolve(cwd, source.path).read_bytes().decode("utf-8")
            except (OSError, UnicodeDecodeError) as error:
                reason = _reason(error) if isinstance(error, OSError) else str(error)
                return HsqlError_Usage(message=f"could not read {source.path}: {reason}")
        statements.extend(split_statements(text))
    return statements


def _timeout(cells: dict[str, bool], guard: threading.Lock, connection: Connection) -> None:
    with guard:
        if not cells["running"]:
            return
        cells["timed_out"] = True
    cancel_queries(connection)


def _log_start(connection: Connection, context: HsqlContext, sql: str, run_at: str) -> int | None:
    logged = record_query(context.query_log, QueryRecord(run_at=run_at, program="hsql", connection=connection.connection_id, profile=context.profile, adapter=context.adapter_name, sql=redact_sql(sql, context.secrets), status=QueryStatus_Ok(), rows=Nothing(), truncated=Nothing(), elapsed_ms=Nothing(), error_text=Nothing()))
    return logged.value if isinstance(logged, Ok) else None


def _log_end(context: HsqlContext, row: int | None, status: QueryStatus, result: ResultSet | None, failure: str | None) -> None:
    if row is not None:
        update_query(context.query_log, row, status, Some(value=result.fetched_row_count) if result is not None else Nothing(), Some(value=result.truncated) if result is not None else Nothing(), Some(value=float(result.elapsed_ms)) if result is not None else Nothing(), Some(value=redact_text(failure, context.secrets)) if failure is not None else Nothing())


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


def _suffix(fmt: str) -> str:
    if fmt in ("table", "vertical"):
        return ".txt"
    if fmt in ("markdown", "md"):
        return ".md"
    return "." + fmt


def _write(path: pathlib.Path, data: bytes) -> HsqlError | None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    except OSError as error:
        return HsqlError_Usage(message=f"could not write {path}: {_reason(error)}")
    return None


def _export(result: ResultSet, fmt: str, arguments: HsqlArguments) -> bytes | HsqlError:
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
        written = write_result(result, ExportRequest(path=path, format=fmt, options=CottList(values=options)))
        if isinstance(written, Ok):
            try:
                return path.read_bytes()
            except OSError as error:
                return HsqlError_Query(message=f"could not read the exported file: {_reason(error)}")
        failure = written.error
        if isinstance(failure, ExportError_UnknownFormat):
            return HsqlError_Usage(message=f"unknown format {failure.name}")
        if isinstance(failure, ExportError_InvalidOption):
            return HsqlError_Usage(message=f"invalid {failure.name} option: {failure.message}")
        if isinstance(failure, ExportError_PathIsDirectory):
            return HsqlError_Query(message=f"{failure.path} is a directory")
        return HsqlError_Query(message=f"{failure.title}\n{failure.message}")


def _emit(results: list[ResultSet], arguments: HsqlArguments, cwd: pathlib.Path, context: HsqlContext) -> tuple[bytes, list[str], HsqlError | None]:
    fmt = arguments.format
    layouts = ("table", "markdown", "md", "vertical")
    single = ("csv", "tsv", "json", "jsonl", "ndjson", "parquet", "orc", "feather", "arrow")
    selected, error = _select(results, arguments.result)
    notes: list[str] = []
    if error is not None:
        return b"", notes, error
    directory: pathlib.Path | None = None
    output_file: pathlib.Path | None = None
    if isinstance(arguments.output, Some):
        target = _resolve(cwd, arguments.output.value)
        if target.is_dir() or arguments.output.value.endswith(os.sep):
            directory = target
        else:
            output_file = target
    if fmt not in layouts and isinstance(arguments.display_rows, Some):
        notes.append("note: --display-rows only applies to text layouts; use --limit to fetch fewer rows.\n")
    if fmt in single and len(selected) > 1 and directory is None:
        return b"", notes, HsqlError_Usage(message=f"{len(selected)} result sets, but {fmt} holds one; use --result last, --result N, or -o DIR for one file each")
    chunks: list[bytes] = []
    if fmt != "none":
        for index, result in enumerate(selected, 1):
            if fmt in layouts:
                display = arguments.display_rows
                cap: Some[U64] | Nothing = Nothing() if isinstance(display, Some) and display.value < 0 else Some(value=display.value if isinstance(display, Some) else 10 if fmt == "vertical" else 40)
                footer = not (arguments.tuples_only or arguments.no_footer)
                options = LayoutOptions(header=not (arguments.tuples_only or arguments.no_header), footer=footer, aligned=not arguments.no_align, null_string=arguments.null_string, color=arguments.color == "always" or (arguments.color == "auto" and context.stdout_tty and not context.no_color and directory is None and output_file is None), max_rows=cap)
                data = layout_text(result, fmt, options).encode("utf-8")
                if not footer and isinstance(cap, Some) and result.fetched_row_count > cap.value:
                    notes.append(f"note: printed {cap.value} of {result.fetched_row_count} rows; pass --display-rows -1 for all of them\n")
            else:
                exported = _export(result, fmt, arguments)
                if not isinstance(exported, bytes):
                    return b"" if output_file is not None else b"".join(chunks), notes, exported
                data = exported
            if directory is not None:
                path = directory / f"result-{index}{_suffix(fmt)}"
                failure = _write(path, data)
                if failure is not None:
                    return b"", notes, failure
                notes.append(f"note: wrote {path}\n")
            else:
                chunks.append(data)
    if any(result.truncated for result in results):
        notes.append(f"note: results truncated at --limit {arguments.limit}; pass --limit -1 for all rows\n")
    body = b"\n".join(chunks) if fmt in layouts else b"".join(chunks)
    if output_file is not None and fmt != "none":
        return b"", notes, _write(output_file, body)
    return body, notes, None


def _failed(arguments: HsqlArguments, started: float, error: HsqlError) -> tuple[bytes, str, I64]:
    status = _status(error)
    line = hsql_error_line(error)
    if arguments.stats:
        limit: Some[U64] | Nothing = Some(value=arguments.limit) if arguments.limit >= 0 else Nothing()
        line += stats_json("timeout" if status == 4 else "error", 0, 0, False, limit, int((time.monotonic() - started) * 1000), CottList(values=[]), Some(value=line.removeprefix("hsql: error: ").rstrip("\n")))
    return b"", line, status


def _execute(connection: Connection, arguments: HsqlArguments, cwd: pathlib.Path, stdin_text: Some[str] | Nothing, context: HsqlContext) -> tuple[bytes, str, I64]:
    started = time.monotonic()
    read = _sources(arguments, cwd, stdin_text)
    if not isinstance(read, list):
        return _failed(arguments, started, read)
    limit: Some[U64] | Nothing = Some(value=arguments.limit) if arguments.limit >= 0 else Nothing()
    cells = {"running": True, "timed_out": False}
    guard = threading.Lock()
    timeout = arguments.timeout_seconds
    timer: threading.Timer | None = None
    if isinstance(timeout, Some):
        timer = threading.Timer(timeout.value, lambda: _timeout(cells, guard, connection))
        timer.daemon = True
        timer.start()
    results: list[ResultSet] = []
    errors: list[HsqlError] = []
    count = 0
    run_at = datetime.now(timezone.utc).isoformat()
    try:
        for executed in execute_statements(connection, CottList(values=read), limit, arguments.continue_on_error):
            count += 1
            row = _log_start(connection, context, executed.sql, run_at) if arguments.write_history else None
            failure = executed.failure
            title: str | None = None
            message = ""
            if isinstance(failure, Some):
                title, message = failure.value.title, failure.value.message
            elif isinstance(executed.cursor, Some):
                fetched = fetch_result(connection, executed, limit, Nothing())
                if isinstance(fetched, Ok):
                    results.append(fetched.value)
                    _log_end(context, row, QueryStatus_Ok(), fetched.value, None)
                else:
                    title, message = fetched.error.title, fetched.error.message
            else:
                _log_end(context, row, QueryStatus_Ok(), None, None)
            if title is not None:
                if cells["timed_out"] and isinstance(timeout, Some):
                    errors.append(HsqlError_Timeout(message=f"timed out after {timeout.value:g}s"))
                else:
                    errors.append(HsqlError_Query(message=f"{title}\n{message}"))
                _log_end(context, row, QueryStatus_Canceled() if title == "Query canceled" or cells["timed_out"] else QueryStatus_Error(), None, f"{title}\n{message}")
    finally:
        with guard:
            cells["running"] = False
        if timer is not None:
            timer.cancel()
            timer.join()
    if cells["timed_out"] and isinstance(timeout, Some) and not any(isinstance(error, HsqlError_Timeout) for error in errors):
        errors.append(HsqlError_Timeout(message=f"timed out after {timeout.value:g}s"))
    stdout, notes, write_error = _emit(results, arguments, cwd, context)
    if write_error is not None:
        errors.append(write_error)
    timed_out = next((error for error in errors if isinstance(error, HsqlError_Timeout)), None)
    reported = timed_out if timed_out is not None else errors[0] if errors else None
    status = _status(reported) if reported is not None else 0
    stderr = "".join(notes) + "".join(hsql_error_line(error) for error in errors)
    if arguments.stats:
        first = Some(value=hsql_error_line(reported).removeprefix("hsql: error: ").rstrip("\n")) if reported is not None else Nothing()
        stderr += stats_json("ok" if status == 0 else "timeout" if status == 4 else "error", count, sum(result.fetched_row_count for result in results), any(result.truncated for result in results), limit, int((time.monotonic() - started) * 1000), results[-1].columns if results else CottList(values=[]), first)
    return stdout, stderr, status


def _kind(kind: CatalogKind) -> str:
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


def _catalog_result(rows: list[tuple[str, CatalogEntry]], elapsed: U64) -> ResultSet:
    pa: Any = pyarrow
    names = ["path", "name", "query_name", "type", "type_label"]
    values = [[path for path, _ in rows], [entry.label for _, entry in rows], [entry.query_name for _, entry in rows], [_kind(entry.kind) for _, entry in rows], [entry.type_label for _, entry in rows]]
    arrays: list[object] = [cast(object, pa.array(column, type=pa.string())) for column in values]
    raw = cast(object, pa.Table.from_arrays(arrays, names=names))
    if not isinstance(raw, pyarrow.Table):
        raise TypeError("catalog results are not an Arrow table")
    count = len(rows)
    return ResultSet(statement="", columns=CottList(values=[ColumnInfo(name=name, type_label="s") for name in names]), data=Opaque(tag="harlequin.arrow_table", value=raw), row_count=count, fetched_row_count=count, truncated=False, elapsed_ms=elapsed)


def _walk(connection: Connection, segments: list[str]) -> tuple[CottList[CatalogEntry], list[str], str | None] | HsqlError:
    loaded = load_catalog(connection)
    if not isinstance(loaded, Ok):
        return HsqlError_Query(message=f"{loaded.error.title}\n{loaded.error.message}")
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
            return HsqlError_Usage(message=missing_label_message(segment, Some(value=".".join(spelled)) if spelled else Nothing(), CottList(values=[kid.label for kid in kids])))
        spelled.append(spell_catalog_label(segment))
        parent_id = match.id
        if match.expandable and not match.loaded:
            children = load_catalog_children(connection, match)
            if not isinstance(children, Ok):
                return HsqlError_Query(message=f"{children.error.title}\n{children.error.message}")
            catalog = replace_children(catalog, match.id, children.value)
    return catalog, spelled, parent_id


def _chain(entry: CatalogEntry, by_id: dict[str, CatalogEntry]) -> list[str]:
    labels = [entry.label]
    current = entry
    while isinstance(current.parent, Some) and current.parent.value in by_id:
        current = by_id[current.parent.value]
        labels.append(current.label)
    labels.reverse()
    return labels


def _catalog(connection: Connection, arguments: HsqlArguments, cwd: pathlib.Path, context: HsqlContext) -> tuple[bytes, str, I64]:
    started = time.monotonic()
    parsed = parse_catalog_path(arguments.catalog_path.value if isinstance(arguments.catalog_path, Some) else "")
    if not isinstance(parsed, Ok):
        return _failed(arguments, started, parsed.error)
    segments = [segment for segment in parsed.value.segments]
    pattern = parsed.value.pattern
    rows: list[tuple[str, CatalogEntry]] = []
    mode = arguments.mode
    if isinstance(mode, HsqlMode_CatalogSearch):
        if segments:
            walked = _walk(connection, segments)
            if not isinstance(walked, tuple):
                return _failed(arguments, started, walked)
        found = search_catalog(connection, mode.term)
        if not isinstance(found, Ok):
            return _failed(arguments, started, HsqlError_Query(message=f"{found.error.title}\n{found.error.message}"))
        entries = normalize_catalog(found.value)
        by_id = {entry.id: entry for entry in entries}
        depth = len(segments)
        for entry in entries:
            labels = _chain(entry, by_id)
            if len(labels) <= depth or labels[:depth] != segments:
                continue
            if isinstance(pattern, Some) and not fnmatch.fnmatchcase(labels[depth], pattern.value):
                continue
            rows.append((".".join(spell_catalog_label(label) for label in labels), entry))
    else:
        walked = _walk(connection, segments)
        if not isinstance(walked, tuple):
            return _failed(arguments, started, walked)
        catalog, spelled, parent_id = walked
        for entry in catalog_children(catalog, Some(value=parent_id) if parent_id is not None else Nothing()):
            if isinstance(pattern, Some) and not fnmatch.fnmatchcase(entry.label, pattern.value):
                continue
            rows.append((".".join([*spelled, spell_catalog_label(entry.label)]), entry))
    result = _catalog_result(rows, int((time.monotonic() - started) * 1000))
    stdout, notes, error = _emit([result], arguments, cwd, context)
    status = _status(error) if error is not None else 0
    stderr = "".join(notes) + (hsql_error_line(error) if error is not None else "")
    if arguments.stats:
        limit: Some[U64] | Nothing = Some(value=arguments.limit) if arguments.limit >= 0 else Nothing()
        failure: Some[str] | Nothing = Some(value=hsql_error_line(error).removeprefix("hsql: error: ").rstrip("\n")) if error is not None else Nothing()
        stderr += stats_json("ok" if status == 0 else "error", 0, len(rows), False, limit, int((time.monotonic() - started) * 1000), result.columns, failure)
    return stdout, stderr, status


def execute_hsql_request(connection: Connection, arguments: HsqlArguments, cwd: pathlib.Path, stdin_text: Some[str] | Nothing, context: HsqlContext) -> HsqlResponse:
    started = time.monotonic()
    try:
        if isinstance(arguments.mode, HsqlMode_Execute):
            stdout, stderr, status = _execute(connection, arguments, cwd, stdin_text, context)
        elif isinstance(arguments.mode, (HsqlMode_Catalog, HsqlMode_CatalogSearch)):
            stdout, stderr, status = _catalog(connection, arguments, cwd, context)
        else:
            stdout, stderr, status = _failed(arguments, started, HsqlError_Usage(message="this mode does not run SQL on a connection"))
    except KeyboardInterrupt:
        stdout, stderr, status = _failed(arguments, started, HsqlError_Interrupted())
    except Exception as error:
        stdout, stderr, status = _failed(arguments, started, HsqlError_Crash(message=str(error)))
    return HsqlResponse(stdout=stdout, stderr=redact_text(stderr, context.secrets), status=status)
