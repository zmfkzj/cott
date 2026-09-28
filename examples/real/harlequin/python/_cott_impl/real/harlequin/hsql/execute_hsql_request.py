import fnmatch
import os
import pathlib
import threading
import time
from datetime import datetime, timezone

from cott_runtime import CottContractViolation, CottList, I64, Nothing, Ok, Option, Some, U64, _cott_fixture_read, _cott_fixture_remove, _cott_fixture_write
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
from real.harlequin.results import result_set_from_rows
from real.harlequin.results_types import CellValue, CellValue_Text, ColumnInfo, ResultSet
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


def _limit(arguments: HsqlArguments) -> Option[U64]:
    return Some(value=arguments.limit) if arguments.limit >= 0 else Nothing()


def _elapsed(start: float) -> U64:
    return max(0, int((time.monotonic() - start) * 1000))


def _resolve(cwd: pathlib.Path, name: str) -> pathlib.Path:
    path = pathlib.Path(name).expanduser()
    return path if path.is_absolute() else cwd / path


def _reason(error: OSError) -> str:
    return error.strerror if error.strerror else str(error)


def _read_bytes(path: pathlib.Path) -> bytes:
    try:
        return _cott_fixture_read(path)
    except CottContractViolation as violation:
        if violation.message == "fixture adapters are inactive":
            return path.read_bytes()
        cause = violation.__cause__
        if isinstance(cause, OSError):
            raise cause
        raise


def _sources(arguments: HsqlArguments, cwd: pathlib.Path, stdin_text: Option[str]) -> list[str] | HsqlError:
    statements: list[str] = []
    for source in arguments.sources:
        if isinstance(source, SqlSource_Command):
            text = source.sql
        elif source.path == "-":
            text = stdin_text.value if isinstance(stdin_text, Some) else ""
        else:
            try:
                text = _read_bytes(_resolve(cwd, source.path)).decode("utf-8")
            except OSError as error:
                return HsqlError_Usage(message=f"could not read {source.path}: {_reason(error)}")
            except (UnicodeDecodeError, CottContractViolation) as error:
                reason = error.message if isinstance(error, CottContractViolation) else str(error)
                return HsqlError_Usage(message=f"could not read {source.path}: {reason}")
        statements.extend(split_statements(text))
    return statements


def _timeout(cells: dict[str, bool], guard: threading.Lock, connection: Connection) -> None:
    with guard:
        if not cells["running"]:
            return
        cells["timed_out"] = True
    cancel_queries(connection)


def _log_start(connection: Connection, context: HsqlContext, sql: str, run_at: str) -> I64 | None:
    recorded = record_query(context.query_log, QueryRecord(
        run_at=run_at, program="hsql", connection=connection.connection_id,
        profile=context.profile, adapter=context.adapter_name,
        sql=redact_sql(sql, context.secrets), status=QueryStatus_Ok(), rows=Nothing(),
        truncated=Nothing(), elapsed_ms=Nothing(), error_text=Nothing(),
    ))
    return recorded.value if isinstance(recorded, Ok) else None


def _log_end(context: HsqlContext, row: I64 | None, status: QueryStatus, result: ResultSet | None, failure: str | None) -> None:
    if row is not None:
        update_query(
            context.query_log, row, status,
            Some(value=result.fetched_row_count) if result is not None else Nothing(),
            Some(value=result.truncated) if result is not None else Nothing(),
            Some(value=float(result.elapsed_ms)) if result is not None else Nothing(),
            Some(value=redact_text(failure, context.secrets)) if failure is not None else Nothing(),
        )


def _select(results: list[ResultSet], choice: str) -> tuple[list[ResultSet], HsqlError | None]:
    if choice == "all":
        return results, None
    if choice == "last":
        return results[-1:], None
    try:
        number = int(choice)
    except ValueError:
        return [], HsqlError_Usage(message="--result must be all, last, or a result number.")
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
        try:
            _cott_fixture_write(path, data)
        except CottContractViolation as violation:
            if violation.message != "fixture adapters are inactive":
                cause = violation.__cause__
                if isinstance(cause, OSError):
                    raise cause
                raise
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    except OSError as error:
        return HsqlError_Usage(message=f"could not write {path}: {_reason(error)}")
    except CottContractViolation as error:
        return HsqlError_Usage(message=f"could not write {path}: {error.message}")
    return None


def _directory(path: pathlib.Path) -> bool | HsqlError:
    try:
        _cott_fixture_read(path)
        return False
    except CottContractViolation as violation:
        if violation.message == "fixture adapters are inactive":
            return path.is_dir()
        cause = violation.__cause__
        if isinstance(cause, IsADirectoryError):
            return True
        if isinstance(cause, FileNotFoundError):
            return False
        if isinstance(cause, OSError):
            return HsqlError_Usage(message=f"could not inspect {path}: {_reason(cause)}")
        return HsqlError_Usage(message=f"could not inspect {path}: {violation.message}")
    except IsADirectoryError:
        return True
    except FileNotFoundError:
        return False
    except OSError as error:
        return HsqlError_Usage(message=f"could not inspect {path}: {_reason(error)}")


def _remove_export(path: pathlib.Path) -> None:
    try:
        _cott_fixture_remove(path)
    except CottContractViolation as violation:
        if violation.message == "fixture adapters are inactive":
            try:
                path.unlink()
            except FileNotFoundError:
                return
        elif isinstance(violation.__cause__, FileNotFoundError):
            return
        else:
            raise


def _export(result: ResultSet, fmt: str, arguments: HsqlArguments) -> bytes | HsqlError:
    options: list[ExportOptionValue] = []
    if fmt in ("csv", "tsv"):
        null = arguments.null_string
        options.append(ExportOptionValue(name="na_rep", value=null.value if isinstance(null, Some) else ""))
        if arguments.tuples_only or arguments.no_header:
            options.append(ExportOptionValue(name="header", value="false"))
    if fmt == "json":
        options.append(ExportOptionValue(name="array", value="true"))
    path = pathlib.Path(f".hsql-export-{os.getpid()}-{time.monotonic_ns()}-{threading.get_ident()}{_suffix(fmt)}")
    try:
        written = write_result(result, ExportRequest(path=path, format=fmt, options=CottList(values=options)))
        if not isinstance(written, Ok):
            failure = written.error
            if isinstance(failure, ExportError_UnknownFormat):
                return HsqlError_Usage(message=f"unknown format {failure.name}")
            if isinstance(failure, ExportError_InvalidOption):
                return HsqlError_Usage(message=f"invalid {failure.name} option: {failure.message}")
            if isinstance(failure, ExportError_PathIsDirectory):
                return HsqlError_Query(message=f"{failure.path} is a directory")
            return HsqlError_Query(message=f"{failure.title}\n{failure.message}")
        return _read_bytes(path)
    except OSError as error:
        return HsqlError_Query(message=f"could not read the exported file: {_reason(error)}")
    except CottContractViolation as error:
        return HsqlError_Query(message=f"could not read the exported file: {error.message}")
    finally:
        _remove_export(path)


def _emit(results: list[ResultSet], arguments: HsqlArguments, cwd: pathlib.Path, context: HsqlContext) -> tuple[bytes, list[str], HsqlError | None]:
    fmt = arguments.format
    layouts = ("table", "markdown", "md", "vertical")
    single = ("csv", "tsv", "json", "parquet", "orc", "feather", "arrow")
    selected, selection_error = _select(results, arguments.result)
    notes: list[str] = []
    if any(result.truncated for result in results):
        notes.append(f"note: results truncated at --limit {arguments.limit}; pass --limit -1 for all rows\n")
    if selection_error is not None:
        return b"", notes, selection_error
    directory: pathlib.Path | None = None
    output_file: pathlib.Path | None = None
    if fmt != "none" and isinstance(arguments.output, Some):
        target = _resolve(cwd, arguments.output.value)
        if arguments.output.value.endswith(os.sep):
            directory = target
        else:
            classified = _directory(target)
            if not isinstance(classified, bool):
                return b"", notes, classified
            if classified:
                directory = target
            else:
                output_file = target
    if fmt not in layouts and isinstance(arguments.display_rows, Some):
        notes.append("note: --display-rows only applies to text layouts; use --limit to fetch fewer rows.\n")
    if fmt in single and len(selected) > 1 and directory is None:
        return b"", notes, HsqlError_Usage(message=f"{len(selected)} result sets, but {fmt} holds one; use --result last, --result N, or -o DIR for one file each")
    chunks: list[bytes] = []
    if fmt != "none":
        for index, result in enumerate(selected, start=1):
            if fmt in layouts:
                display = arguments.display_rows
                cap: Option[U64] = Nothing() if isinstance(display, Some) and display.value < 0 else Some(value=display.value if isinstance(display, Some) else 10 if fmt == "vertical" else 40)
                footer = not (arguments.tuples_only or arguments.no_footer)
                color = arguments.color == "always" or (arguments.color == "auto" and context.stdout_tty and not context.no_color and directory is None and output_file is None)
                options = LayoutOptions(header=not (arguments.tuples_only or arguments.no_header), footer=footer, aligned=not arguments.no_align, null_string=arguments.null_string, color=color, max_rows=cap)
                data = layout_text(result, fmt, options).encode("utf-8")
                if not footer and isinstance(cap, Some) and result.fetched_row_count > cap.value:
                    notes.append(f"note: printed {cap.value} of {result.fetched_row_count} rows; pass --display-rows -1 for all of them\n")
            else:
                exported = _export(result, fmt, arguments)
                if not isinstance(exported, bytes):
                    return b"" if output_file is not None or directory is not None else b"".join(chunks), notes, exported
                data = exported
            if directory is not None:
                path = directory / f"result-{index}{_suffix(fmt)}"
                write_error = _write(path, data)
                if write_error is not None:
                    return b"", notes, write_error
                notes.append(f"note: wrote {path}\n")
            else:
                chunks.append(data)
    body = b"\n".join(chunks) if fmt in layouts else b"".join(chunks)
    if output_file is not None:
        return b"", notes, _write(output_file, body)
    return body, notes, None


def _failure_response(arguments: HsqlArguments, started: float, error: HsqlError) -> tuple[bytes, str, I64]:
    status = _status(error)
    line = hsql_error_line(error)
    if arguments.stats:
        line += stats_json("timeout" if status == 4 else "error", 0, 0, False, _limit(arguments), _elapsed(started), CottList(values=[]), Some(value=line.removeprefix("hsql: error: ").rstrip("\n")))
    return b"", line, status


def _execute(connection: Connection, arguments: HsqlArguments, cwd: pathlib.Path, stdin_text: Option[str], context: HsqlContext) -> tuple[bytes, str, I64]:
    started = time.monotonic()
    sources = _sources(arguments, cwd, stdin_text)
    if not isinstance(sources, list):
        return _failure_response(arguments, started, sources)
    limit = _limit(arguments)
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
    run_at = datetime.now(timezone.utc).isoformat(timespec="microseconds") if arguments.write_history else ""
    try:
        for executed in execute_statements(connection, CottList(values=sources), limit, arguments.continue_on_error):
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
                    if not any(isinstance(error, HsqlError_Timeout) for error in errors):
                        errors.append(HsqlError_Timeout(message=f"timed out after {timeout.value:g}s"))
                else:
                    errors.append(HsqlError_Query(message=f"{title}\n{message}"))
                outcome: QueryStatus = QueryStatus_Canceled() if title == "Query canceled" or cells["timed_out"] else QueryStatus_Error()
                _log_end(context, row, outcome, None, f"{title}\n{message}")
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
        failure_text: Option[str] = Some(value=hsql_error_line(reported).removeprefix("hsql: error: ").rstrip("\n")) if reported is not None else Nothing()
        stderr += stats_json("ok" if status == 0 else "timeout" if status == 4 else "error", count, sum(result.fetched_row_count for result in results), any(result.truncated for result in results), limit, _elapsed(started), results[-1].columns if results else CottList(values=[]), failure_text)
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
    columns = CottList(values=[ColumnInfo(name=name, type_label="s") for name in ("path", "name", "query_name", "type", "type_label")])
    values: list[CottList[CellValue]] = []
    for path, entry in rows:
        values.append(CottList(values=[CellValue_Text(value=text) for text in (path, entry.label, entry.query_name, _kind(entry.kind), entry.type_label)]))
    return result_set_from_rows("", columns, CottList(values=values), Nothing(), elapsed)


def _walk(connection: Connection, segments: list[str]) -> tuple[CottList[CatalogEntry], list[str], str | None] | HsqlError:
    loaded = load_catalog(connection)
    if not isinstance(loaded, Ok):
        return HsqlError_Query(message=f"{loaded.error.title}\n{loaded.error.message}")
    catalog = normalize_catalog(loaded.value)
    parent_id: str | None = None
    spelled: list[str] = []
    for segment in segments:
        siblings = catalog_children(catalog, Some(value=parent_id) if parent_id is not None else Nothing())
        match: CatalogEntry | None = None
        for child in siblings:
            if child.label == segment:
                match = child
                break
        if match is None:
            return HsqlError_Usage(message=missing_label_message(segment, Some(value=".".join(spelled)) if spelled else Nothing(), CottList(values=[child.label for child in siblings])))
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
        return _failure_response(arguments, started, parsed.error)
    segments = [segment for segment in parsed.value.segments]
    pattern = parsed.value.pattern
    rows: list[tuple[str, CatalogEntry]] = []
    if isinstance(arguments.mode, HsqlMode_CatalogSearch):
        if segments:
            walked = _walk(connection, segments)
            if not isinstance(walked, tuple):
                return _failure_response(arguments, started, walked)
        found = search_catalog(connection, arguments.mode.term)
        if not isinstance(found, Ok):
            return _failure_response(arguments, started, HsqlError_Query(message=f"{found.error.title}\n{found.error.message}"))
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
            return _failure_response(arguments, started, walked)
        catalog, spelled, parent_id = walked
        for entry in catalog_children(catalog, Some(value=parent_id) if parent_id is not None else Nothing()):
            if isinstance(pattern, Some) and not fnmatch.fnmatchcase(entry.label, pattern.value):
                continue
            rows.append((".".join([*spelled, spell_catalog_label(entry.label)]), entry))
    result = _catalog_result(rows, _elapsed(started))
    stdout, notes, error = _emit([result], arguments, cwd, context)
    status = _status(error) if error is not None else 0
    stderr = "".join(notes) + (hsql_error_line(error) if error is not None else "")
    if arguments.stats:
        failure: Option[str] = Some(value=hsql_error_line(error).removeprefix("hsql: error: ").rstrip("\n")) if error is not None else Nothing()
        stderr += stats_json("ok" if status == 0 else "error", 0, len(rows), False, _limit(arguments), _elapsed(started), result.columns, failure)
    return stdout, stderr, status


def execute_hsql_request(connection: Connection, arguments: HsqlArguments, cwd: pathlib.Path, stdin_text: Option[str], context: HsqlContext) -> HsqlResponse:
    started = time.monotonic()
    try:
        if isinstance(arguments.mode, HsqlMode_Execute):
            stdout, stderr, status = _execute(connection, arguments, cwd, stdin_text, context)
        elif isinstance(arguments.mode, (HsqlMode_Catalog, HsqlMode_CatalogSearch)):
            stdout, stderr, status = _catalog(connection, arguments, cwd, context)
        else:
            stdout, stderr, status = _failure_response(arguments, started, HsqlError_Usage(message="this mode does not run SQL on a connection"))
    except KeyboardInterrupt:
        stdout, stderr, status = _failure_response(arguments, started, HsqlError_Interrupted())
    except Exception as error:
        stdout, stderr, status = _failure_response(arguments, started, HsqlError_Crash(message=str(error)))
    return HsqlResponse(stdout=stdout, stderr=redact_text(stderr, context.secrets), status=status)
