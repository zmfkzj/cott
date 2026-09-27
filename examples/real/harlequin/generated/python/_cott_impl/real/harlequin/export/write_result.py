import pathlib
import shutil
import tempfile
from typing import Any, Final, cast

import duckdb
import pyarrow
import pyarrow.feather
import pyarrow.orc
from cott_runtime import CottContractViolation, Err, Ok, Result, _cott_fixture_write

from real.harlequin.export_types import ExportError, ExportError_InvalidOption, ExportError_PathIsDirectory, ExportError_UnknownFormat, ExportError_WriteFailed, ExportReceipt, ExportRequest
from real.harlequin.results_types import ResultSet

_TAG: Final[str] = "harlequin.arrow_table"
_CSV_TITLE: Final[str] = "DuckDB raised an error when writing your query to a CSV file."
_JSON_TITLE: Final[str] = "DuckDB raised an error when writing your query to a JSON file."
_PARQUET_TITLE: Final[str] = "DuckDB raised an error when writing your query to a Parquet file."
_ORC_TITLE: Final[str] = "Arrow raised an error when writing your data to an ORC file."
_FEATHER_TITLE: Final[str] = "Arrow raised an error when writing your data to a Feather file."
_CSV_KEYS: Final[str] = "header,sep,compression,quotechar,escapechar,na_rep,encoding,date_format,timestamp_format,quoting"
_JSON_KEYS: Final[str] = "array,compression,date_format,timestamp_format"
_ORC_KEYS: Final[str] = "file_version,batch_size,stripe_size,compression,compression_block_size,compression_strategy,row_index_stride,padding_tolerance,dictionary_key_size_threshold,bloom_filter_columns,bloom_filter_fpp"
_ORC_INTS: Final[str] = "batch_size,stripe_size,compression_block_size,row_index_stride"
_ORC_FLOATS: Final[str] = "padding_tolerance,dictionary_key_size_threshold,bloom_filter_fpp"
_FEATHER_KEYS: Final[str] = "compression,compression_level,chunksize,version"
_FEATHER_INTS: Final[str] = "compression_level,chunksize,version"


def _fail(title: str, exc: BaseException) -> Result[ExportReceipt, ExportError]:
    return Err(error=ExportError_WriteFailed(title=title, message=str(exc)))


def _dedupe(names: list[str]) -> list[str]:
    used: set[str] = set()
    next_suffix: dict[str, int] = {}
    result: list[str] = []
    for name in names:
        if name not in used:
            used.add(name)
            next_suffix[name] = 0
            result.append(name)
            continue
        suffix = next_suffix.get(name, 0)
        candidate = f"{name}{suffix}"
        while candidate in used:
            suffix += 1
            candidate = f"{name}{suffix}"
        next_suffix[name] = suffix + 1
        used.add(candidate)
        result.append(candidate)
    return result


def _options(request: ExportRequest, keys: str) -> dict[str, object]:
    allowed = keys.split(",")
    parsed: dict[str, object] = {}
    for option in request.options:
        if option.name not in allowed or option.value == "":
            continue
        lower = option.value.lower()
        if lower == "true":
            parsed[option.name] = True
        elif lower == "false":
            parsed[option.name] = False
        else:
            parsed[option.name] = option.value
    return parsed


def _convert(opts: dict[str, object], ints: str, floats: str) -> ExportError | None:
    for name in ints.split(","):
        if name in opts:
            try:
                opts[name] = int(str(opts[name]))
            except ValueError as exc:
                return ExportError_InvalidOption(name=name, message=str(exc))
    for name in floats.split(","):
        if name in opts:
            try:
                opts[name] = float(str(opts[name]))
            except ValueError as exc:
                return ExportError_InvalidOption(name=name, message=str(exc))
    return None


def _export_table(result_set: ResultSet) -> object:
    handle = result_set.data
    if handle.tag != _TAG:
        raise TypeError(f"ResultSet.data must be tagged {_TAG}, got {handle.tag}")
    payload: object = handle.unwrap()
    arrow: Any = pyarrow
    if not isinstance(payload, arrow.Table):
        raise TypeError("ResultSet.data must contain a pyarrow.Table")
    table: Any = payload
    raw_names: object = cast(object, table.column_names)
    if not isinstance(raw_names, list):
        raise TypeError("Arrow column names must be a list")
    for name in cast(list[object], raw_names):
        if not isinstance(name, str):
            raise TypeError("Arrow column names must be strings")
    names = cast(list[str], raw_names)
    if len(set(names)) == len(names):
        return payload
    renamed: object = cast(object, table.rename_columns(_dedupe(names)))
    if not isinstance(renamed, arrow.Table):
        raise TypeError("Arrow rename must return a pyarrow.Table")
    return renamed


def _write_to_path(table: object, fmt: str, file_name: str, opts: dict[str, object]) -> None:
    if fmt in ("csv", "tsv"):
        header = opts.pop("header", True) is not False
        quoting = opts.pop("quoting", False)
        if quoting is True:
            opts["quoting"] = "ALL"
        if fmt == "tsv" and "sep" not in opts:
            opts["sep"] = "\t"
        con = duckdb.connect(config={"threads": 1})
        try:
            csv_relation: Any = con.from_arrow(table)
            csv_relation.write_csv(file_name, header=header, **opts)
        finally:
            con.close()
        return
    if fmt in ("json", "jsonl", "ndjson"):
        clauses = "FORMAT JSON"
        params: list[object] = [file_name]
        if fmt == "json" and opts.get("array") is True:
            clauses += ", ARRAY TRUE"
        if "compression" in opts:
            clauses += ", COMPRESSION ?"
            params.append(str(opts["compression"]))
        if "date_format" in opts:
            clauses += ", DATEFORMAT ?"
            params.append(str(opts["date_format"]))
        if "timestamp_format" in opts:
            clauses += ", TIMESTAMPFORMAT ?"
            params.append(str(opts["timestamp_format"]))
        con = duckdb.connect(config={"threads": 1})
        try:
            con.register("data", table)
            con.execute(f"COPY (select * from data) TO ? ({clauses})", params)
        finally:
            con.close()
        return
    if fmt == "parquet":
        con = duckdb.connect(config={"threads": 1})
        try:
            parquet_relation: Any = con.from_arrow(table)
            parquet_relation.write_parquet(file_name, **opts)
        finally:
            con.close()
        return
    if fmt == "orc":
        orc: Any = pyarrow.orc
        orc.write_table(table, file_name, **opts)
        return
    feather: Any = pyarrow.feather
    feather.write_feather(table, file_name, **opts)


def write_result(result_set: ResultSet, request: ExportRequest) -> Result[ExportReceipt, ExportError]:
    fmt = request.format.lower()
    if fmt not in ("csv", "tsv", "json", "jsonl", "ndjson", "parquet", "orc", "feather", "arrow"):
        return Err(error=ExportError_UnknownFormat(name=request.format))
    target = request.path.expanduser()
    if fmt in ("csv", "tsv"):
        title = _CSV_TITLE
        opts = _options(request, _CSV_KEYS)
    elif fmt in ("json", "jsonl", "ndjson"):
        title = _JSON_TITLE
        opts = _options(request, _JSON_KEYS)
    elif fmt == "parquet":
        title = _PARQUET_TITLE
        opts = _options(request, "compression")
    elif fmt == "orc":
        title = _ORC_TITLE
        opts = _options(request, _ORC_KEYS)
        problem = _convert(opts, _ORC_INTS, _ORC_FLOATS)
        if problem is not None:
            return Err(error=problem)
        if "bloom_filter_columns" in opts:
            opts["bloom_filter_columns"] = [part for column in str(opts["bloom_filter_columns"]).split(",") if (part := column.strip())]
    else:
        title = _FEATHER_TITLE
        opts = _options(request, _FEATHER_KEYS)
        problem = _convert(opts, _FEATHER_INTS, "")
        if problem is not None:
            return Err(error=problem)
        if opts.get("version") == 1 and opts.get("compression") == "uncompressed":
            opts["compression"] = None

    try:
        table = _export_table(result_set)
        with tempfile.TemporaryDirectory() as work:
            temporary = pathlib.Path(work) / (target.name or "result")
            _write_to_path(table, fmt, str(temporary), opts)
            contents = temporary.read_bytes()
            try:
                _cott_fixture_write(request.path, contents)
            except CottContractViolation as exc:
                if exc.message == "fixture adapters are inactive":
                    if target.is_dir():
                        return Err(error=ExportError_PathIsDirectory(path=request.path))
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(temporary, target)
                elif isinstance(exc.__cause__, IsADirectoryError):
                    return Err(error=ExportError_PathIsDirectory(path=request.path))
                elif exc.__cause__ is not None:
                    return _fail(title, exc.__cause__)
                else:
                    return Err(error=ExportError_WriteFailed(title=title, message=exc.message))
    except IsADirectoryError:
        return Err(error=ExportError_PathIsDirectory(path=request.path))
    except Exception as exc:
        return _fail(title, exc)
    return Ok(value=ExportReceipt(path=request.path, rows=result_set.fetched_row_count))
