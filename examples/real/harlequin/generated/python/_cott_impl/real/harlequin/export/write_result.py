import pathlib
from typing import Any, Final, cast

import duckdb
import pyarrow.feather
import pyarrow.orc
from cott_runtime import Err, Ok, Result

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
    seen: dict[str, int] = {}
    used: set[str] = set()
    out: list[str] = []
    for name in names:
        if name not in used:
            used.add(name)
            seen[name] = 0
            out.append(name)
            continue
        n = seen.get(name, 0)
        candidate = f"{name}{n}"
        while candidate in used:
            n += 1
            candidate = f"{name}{n}"
        seen[name] = n + 1
        used.add(candidate)
        out.append(candidate)
    return out


def _parse(request: ExportRequest, allowed: str) -> dict[str, object]:
    keys = allowed.split(",")
    opts: dict[str, object] = {}
    for opt in request.options:
        if opt.value == "" or opt.name not in keys:
            continue
        low = opt.value.lower()
        if low == "true":
            opts[opt.name] = True
        elif low == "false":
            opts[opt.name] = False
        else:
            opts[opt.name] = opt.value
    return opts


def _convert(opts: dict[str, object], ints: str, floats: str) -> ExportError | None:
    for key in ints.split(","):
        if key and key in opts:
            try:
                opts[key] = int(str(opts[key]))
            except ValueError as exc:
                return ExportError_InvalidOption(name=key, message=str(exc))
    for key in floats.split(","):
        if key and key in opts:
            try:
                opts[key] = float(str(opts[key]))
            except ValueError as exc:
                return ExportError_InvalidOption(name=key, message=str(exc))
    return None


def write_result(result_set: ResultSet, request: ExportRequest) -> Result[ExportReceipt, ExportError]:
    fmt = request.format.lower()
    if fmt not in ("csv", "tsv", "json", "jsonl", "ndjson", "parquet", "orc", "feather", "arrow"):
        return Err(error=ExportError_UnknownFormat(name=request.format))
    target = pathlib.Path(request.path).expanduser()
    if target.is_dir():
        return Err(error=ExportError_PathIsDirectory(path=request.path))
    handle = result_set.data
    if handle.tag != _TAG:
        raise TypeError(f"ResultSet.data must be tagged {_TAG}, got {handle.tag}")
    table: Any = handle.unwrap()
    names = [str(n) for n in cast(list[object], table.column_names)]
    deduped = _dedupe(names)
    if deduped != names:
        table = table.rename_columns(deduped)
    receipt = ExportReceipt(path=request.path, rows=result_set.fetched_row_count)
    file_name = str(target)

    if fmt in ("csv", "tsv"):
        opts = _parse(request, _CSV_KEYS)
        header = opts.pop("header", True) is not False
        quoting = opts.pop("quoting", False)
        if fmt == "tsv" and "sep" not in opts:
            opts["sep"] = "\t"
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            con = duckdb.connect()
            try:
                rel: Any = con.from_arrow(table)
                rel.write_csv(
                    file_name,
                    header=header,
                    sep=opts.get("sep"),
                    na_rep=opts.get("na_rep"),
                    quotechar=opts.get("quotechar"),
                    escapechar=opts.get("escapechar"),
                    date_format=opts.get("date_format"),
                    timestamp_format=opts.get("timestamp_format"),
                    quoting="ALL" if quoting is True else None,
                    encoding=opts.get("encoding"),
                    compression=opts.get("compression"),
                )
            finally:
                con.close()
        except Exception as exc:
            return _fail(_CSV_TITLE, exc)
        return Ok(value=receipt)

    if fmt in ("json", "jsonl", "ndjson"):
        opts = _parse(request, _JSON_KEYS)
        array = fmt == "json" and opts.get("array") is True
        clauses = "FORMAT JSON"
        params: list[object] = [file_name]
        if array:
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
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            con = duckdb.connect()
            try:
                con.register("data", table)
                con.execute(f"COPY (select * from data) TO ? ({clauses})", params)
            finally:
                con.close()
        except Exception as exc:
            return _fail(_JSON_TITLE, exc)
        return Ok(value=receipt)

    if fmt == "parquet":
        opts = _parse(request, "compression")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            con = duckdb.connect()
            try:
                prel: Any = con.from_arrow(table)
                prel.write_parquet(file_name, compression=opts.get("compression"))
            finally:
                con.close()
        except Exception as exc:
            return _fail(_PARQUET_TITLE, exc)
        return Ok(value=receipt)

    if fmt == "orc":
        opts = _parse(request, _ORC_KEYS)
        problem = _convert(opts, _ORC_INTS, _ORC_FLOATS)
        if problem is not None:
            return Err(error=problem)
        if "bloom_filter_columns" in opts:
            raw_cols = str(opts["bloom_filter_columns"])
            opts["bloom_filter_columns"] = [c.strip() for c in raw_cols.split(",") if c.strip()]
        orc: Any = pyarrow.orc
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            orc.write_table(table, file_name, **opts)
        except Exception as exc:
            return _fail(_ORC_TITLE, exc)
        return Ok(value=receipt)

    opts = _parse(request, _FEATHER_KEYS)
    problem = _convert(opts, _FEATHER_INTS, "")
    if problem is not None:
        return Err(error=problem)
    if opts.get("version") == 1 and opts.get("compression") == "uncompressed":
        opts["compression"] = None
    feather: Any = pyarrow.feather
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        feather.write_feather(table, file_name, **opts)
    except Exception as exc:
        return _fail(_FEATHER_TITLE, exc)
    return Ok(value=receipt)
