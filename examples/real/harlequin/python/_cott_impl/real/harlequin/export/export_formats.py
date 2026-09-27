from cott_runtime import CottList
from real.harlequin.export_types import ExportFormatSpec, ExportOptionKind_Choice, ExportOptionKind_Flag, ExportOptionKind_Text, ExportOptionSpec


def _flag(name: str, label: str, description: str, default: str) -> ExportOptionSpec:
    return ExportOptionSpec(name=name, label=label, description=description, kind=ExportOptionKind_Flag(), default=default, placeholder="", integer=False, number=False, allow_empty=False)


def _text(name: str, label: str, description: str, default: str, placeholder: str, integer: bool, number: bool, allow_empty: bool) -> ExportOptionSpec:
    return ExportOptionSpec(name=name, label=label, description=description, kind=ExportOptionKind_Text(), default=default, placeholder=placeholder, integer=integer, number=number, allow_empty=allow_empty)


def _choice(name: str, label: str, description: str, pairs: list[tuple[str, str]], default: str) -> ExportOptionSpec:
    kind = ExportOptionKind_Choice(values=CottList(values=[value for _, value in pairs]), labels=CottList(values=[label for label, _ in pairs]))
    return ExportOptionSpec(name=name, label=label, description=description, kind=kind, default=default, placeholder="", integer=False, number=False, allow_empty=False)


def _fmt(name: str, label: str, extensions: list[str], options: list[ExportOptionSpec]) -> ExportFormatSpec:
    return ExportFormatSpec(name=name, label=label, extensions=CottList(values=extensions), options=CottList(values=options))


def export_formats() -> CottList[ExportFormatSpec]:
    date_desc = "Specifies the date format to use when writing dates."
    ts_desc = "Specifies the date format to use when writing timestamps."
    csv = _fmt("csv", "CSV", [".csv", ".tsv"], [
        _flag("header", "Header", "Whether or not to write a header for the CSV file.", "true"),
        _text("sep", "Separator", "The separator to be used when writing the file.", ",", "", False, False, False),
        _choice("compression", "Compression", "The compression type for the file.", [("Auto", "auto"), ("gzip", "gzip"), ("zstd", "zstd"), ("No compression", "none")], "auto"),
        _flag("quoting", "Force Quote", "If true, quote all values.", "false"),
        _text("date_format", "Date Format", date_desc, "", "%Y-%m-%d", False, False, False),
        _text("timestamp_format", "Timestamp Format", ts_desc, "", "%c", False, False, False),
        _text("quotechar", "Quote Char", "The quoting character to be used when a data value is quoted.", '"', "", False, False, False),
        _text("escapechar", "Escape Char", "The character that should appear before a character that matches the quote value.", '"', "", False, False, False),
        _text("na_rep", "Null String", "The string that is written to represent a NULL value.", "", "", False, False, False),
        _text("encoding", "Encoding", "Only UTF8 is currently supported by DuckDB.", "UTF8", "", False, False, False),
    ])
    parquet = _fmt("parquet", "Parquet", [".parquet", ".pq"], [
        _choice("compression", "Compression", "The compression format to use.", [("Snappy", "snappy"), ("gzip", "gzip"), ("zstd", "zstd"), ("Uncompressed", "uncompressed")], "snappy"),
    ])
    json = _fmt("json", "JSON", [".json", ".js", ".ndjson"], [
        _flag("array", "Array", "Whether to write a JSON array. If false, newline-delimited JSON is written.", "false"),
        _choice("compression", "Compression", "The compression type for the file.", [("Auto", "auto"), ("gzip", "gzip"), ("zstd", "zstd"), ("Uncompressed", "uncompressed")], "auto"),
        _text("date_format", "Date Format", date_desc, "", "%Y-%m-%d", False, False, False),
        _text("timestamp_format", "Timestamp Format", ts_desc, "", "%c", False, False, False),
    ])
    orc = _fmt("orc", "ORC", [".orc"], [
        _choice("file_version", "File Version", "Determine which ORC file version to use.", [("0.11", "0.11"), ("0.12", "0.12")], "0.12"),
        _text("batch_size", "Batch Size", "Number of rows the ORC writer writes at a time.", "1024", "", True, False, False),
        _text("stripe_size", "Stripe Size", "Size of each ORC stripe in bytes.", "67108864", "", True, False, False),
        _choice("compression", "Compression", "The compression codec.", [("Uncompressed", "UNCOMPRESSED"), ("Snappy", "SNAPPY"), ("zlib", "ZLIB"), ("LZ4", "LZ4"), ("zstd", "zstd")], "UNCOMPRESSED"),
        _text("compression_block_size", "Compression Block Size", "Size of each compression block in bytes.", "65536", "", True, False, False),
        _choice("compression_strategy", "Compression Strategy", "The compression strategy i.e. speed vs size reduction.", [("Speed", "SPEED"), ("Compression", "COMPRESSION")], "SPEED"),
        _text("row_index_stride", "Row Index Stride", "The row index stride i.e. the number of rows per an entry in the row index.", "10000", "", True, False, False),
        _text("padding_tolerance", "Padding Tolerance", "The padding tolerance.", "0.0", "", False, True, False),
        _text("dictionary_key_size_threshold", "Dict Key Size Threshold", "The dictionary key size threshold. 0 to disable dictionary encoding. 1 to always enable dictionary encoding.", "0.0", "", False, True, False),
        _text("bloom_filter_columns", "Bloom Filter Columns", "Comma-separated names of columns that use the bloom filter.", "", "", False, False, False),
        _text("bloom_filter_fpp", "Bloom Filter False-Positive", "Upper limit of the false-positive rate of the bloom filter.", "0.05", "", False, True, False),
    ])
    feather = _fmt("feather", "Feather", [".feather"], [
        _choice("compression", "Compression", "The compression codec.", [("Uncompressed", "uncompressed"), ("LZ4", "lz4"), ("zstd", "zstd")], "uncompressed"),
        _text("compression_level", "Compression Level", "Use a compression level particular to the chosen compressor. If None use the default compression level.", "", "", True, False, True),
        _text("chunksize", "Chunk Size", "For V2 files, the internal maximum size of Arrow RecordBatch chunks when writing the Arrow IPC file format. None means use the default, which is currently 64K.", "", "", True, False, True),
        _choice("version", "File Version", "Feather file version. Version 2 is the current. Version 1 is the more limited legacy format.", [("2", "2"), ("1", "1")], "2"),
    ])
    return CottList(values=[csv, parquet, json, orc, feather])
