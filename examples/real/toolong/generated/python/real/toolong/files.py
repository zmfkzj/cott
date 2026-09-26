from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition

from real.toolong.files_types import DecompressError, DecompressError_Corrupt, FindResult, SaveError, SaveError_WriteFailed, SourceError, SourceError_NotFound, SourceError_OpenFailed, TailChunk, TimeJump, TimestampAt, TimestampBatch
from real.toolong.model_types import ByteSpan, Compression, Compression_Uncompressed, FindQuery, LogSource, LogTimestamp, TabIndex, TimeUnit

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def detect_compression(name: str) -> Compression:
    """The compression Toolong detects from a file name (CPython 3.14
mimetypes.guess_type(name, strict=False) encodings, restated because the
mimetypes module is not importable here). Let ext be the final suffix of
name (os.path.splitext). First, while ext.lower() is ".svgz", ".tgz",
".taz", ".tz", ".tbz2" or ".txz", replace that suffix by ".svg.gz",
".tar.gz", ".tar.gz", ".tar.gz", ".tar.bz2" or ".tar.xz" respectively and
take the new final suffix. Then an ext of exactly ".gz" (case sensitive)
is Gzip, exactly ".bz2" is Bzip2, and anything else is Uncompressed."""
    name = _cott_normalize_f32_abi(name, str, path="$.name")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/files/detect_compression.py", "b867da8ea775dfacf78910e93339b0d49b576aab5e0f57ecea7b4323c951fc2b", "detect_compression", expected_project_name="toolong", expected_cott_symbol="real.toolong.files.detect_compression")
        _result = _implementation(name)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.files.detect_compression"
        if _error.span is None:
            _error.span = {"end_byte":2869,"end_column":1,"end_line":104,"start_byte":2188,"start_column":1,"start_line":90}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.files.detect_compression", phase="implementation-call", span={"end_byte":2869,"end_column":1,"end_line":104,"start_byte":2188,"start_column":1,"start_line":90}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.files.detect_compression", phase="implementation-call", span={"end_byte":2869,"end_column":1,"end_line":104,"start_byte":2188,"start_column":1,"start_line":90}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Compression, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Compression, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def decompress(data: bytes, compression: Compression) -> Result[bytes, DecompressError]:
    """Decompress whole-file content: Gzip with gzip.decompress (multi-member
files concatenate), Bzip2 with bz2.decompress, Uncompressed returns data
unchanged. A decompression failure is DecompressError.Corrupt with str() of
the exception, for example "Not a gzipped file (b'no')"."""
    data = _cott_normalize_f32_abi(data, bytes, path="$.data")
    compression = _cott_normalize_f32_abi(compression, Compression, path="$.compression")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/files/decompress.py", "920f42d14cd09e35ba412f2a5cd1ea3d5c6c915240fa42d534a417fb0269366a", "decompress", expected_project_name="toolong", expected_cott_symbol="real.toolong.files.decompress")
        _result = _implementation(data, compression)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.files.decompress"
        if _error.span is None:
            _error.span = {"end_byte":3418,"end_column":1,"end_line":118,"start_byte":2869,"start_column":1,"start_line":104}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.files.decompress", phase="implementation-call", span={"end_byte":3418,"end_column":1,"end_line":118,"start_byte":2869,"start_column":1,"start_line":104}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.files.decompress", phase="implementation-call", span={"end_byte":3418,"end_column":1,"end_line":118,"start_byte":2869,"start_column":1,"start_line":104}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[bytes, DecompressError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.toolong.files.decompress", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (DecompressError_Corrupt,):
                raise CottContractViolation("returned error is not allowed", symbol="real.toolong.files.decompress", phase="error", span={"end_byte":3418,"end_column":1,"end_line":118,"start_byte":2869,"start_column":1,"start_line":104}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.files.decompress", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.toolong.files.decompress", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is DecompressError_Corrupt:
            _cott_contract_condition(True, "real.toolong.files.decompress", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                content = _cott_match_value.value
                return (_cott_contract_condition((((not (compression == Compression_Uncompressed())) or (content == data))), "real.toolong.files.decompress", "ensures:1"))
            _cott_contract_condition((False), "real.toolong.files.decompress", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.files.decompress", clause="ensures:1", phase="ensures", span={"end_byte":3365,"end_column":95,"end_line":112,"start_byte":3275,"start_column":5,"start_line":112}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[bytes, DecompressError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def open_source(path: Path) -> Result[LogSource, SourceError]:
    """Open a log file the way Toolong's LogFile.open does. name is the final
component of path (pathlib name) and compression is
real.toolong.files.detect_compression(name).

Outside a Cott scenario (the fixture read adapter reports that adapters
are inactive): an Uncompressed file is opened read-only with os.open, its
size is found by seeking its descriptor to the end, descriptor is Some of
that descriptor and can_tail is true. A compressed file is decompressed
with gzip.open / bz2.open in 256 KiB chunks into an anonymous temporary
file (tempfile.TemporaryFile); descriptor is Some of a descriptor on that
unlinked temporary file (the temporary file object itself is closed), size
is the number of decompressed bytes and can_tail is false.

While a Cott scenario file-system fixture is active, path is read through
the fixture, compressed content is decompressed with
real.toolong.files.decompress, descriptor is Nothing, size is the content
length and can_tail is true only for Uncompressed files.

A missing file is SourceError.NotFound(name, message); any other failure
to open, read or decompress is SourceError.OpenFailed(name, message).
message is str() of the underlying exception, e.g. "[Errno 2] No such file
or directory: 'x.log'" (for fixture failures, of the adapter's OSError
cause), or the DecompressError.Corrupt message."""
    path = _cott_normalize_f32_abi(path, Path, path="$.path")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/files/open_source.py", "277dd3e62b350d5463584c14e311fdf2b04d4a65143129f935c7311c071ad083", "open_source", expected_project_name="toolong", expected_cott_symbol="real.toolong.files.open_source")
        _result = _implementation(path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.files.open_source"
        if _error.span is None:
            _error.span = {"end_byte":5087,"end_column":1,"end_line":152,"start_byte":3418,"start_column":1,"start_line":118}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.files.open_source", phase="implementation-call", span={"end_byte":5087,"end_column":1,"end_line":152,"start_byte":3418,"start_column":1,"start_line":118}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.files.open_source", phase="implementation-call", span={"end_byte":5087,"end_column":1,"end_line":152,"start_byte":3418,"start_column":1,"start_line":118}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[LogSource, SourceError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.toolong.files.open_source", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (SourceError_NotFound, SourceError_OpenFailed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.toolong.files.open_source", phase="error", span={"end_byte":5087,"end_column":1,"end_line":152,"start_byte":3418,"start_column":1,"start_line":118}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.files.open_source", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.toolong.files.open_source", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is SourceError_NotFound:
            _cott_contract_condition(True, "real.toolong.files.open_source", "error:2")
        if type(_result) is Err and type(_result.error) is SourceError_OpenFailed:
            _cott_contract_condition(True, "real.toolong.files.open_source", "error:3")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                source = _cott_match_value.value
                return (_cott_contract_condition((((source).path == path)), "real.toolong.files.open_source", "ensures:1"))
            _cott_contract_condition((False), "real.toolong.files.open_source", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.files.open_source", clause="ensures:1", phase="ensures", span={"end_byte":4983,"end_column":53,"end_line":145,"start_byte":4935,"start_column":5,"start_line":145}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[LogSource, SourceError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def close_source(source: LogSource) -> Unit:
    """Close source.descriptor with os.close when it is Some, ignoring OSError.
Nothing to do when it is Nothing."""
    source = _cott_normalize_f32_abi(source, LogSource, path="$.source")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/files/close_source.py", "f140e192a92a92916c809f1075b120e0f78bdcb29763bd07032a29e655ec5b52", "close_source", expected_project_name="toolong", expected_cott_symbol="real.toolong.files.close_source")
        _result = _implementation(source)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.files.close_source"
        if _error.span is None:
            _error.span = {"end_byte":5292,"end_column":1,"end_line":160,"start_byte":5087,"start_column":1,"start_line":152}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.files.close_source", phase="implementation-call", span={"end_byte":5292,"end_column":1,"end_line":160,"start_byte":5087,"start_column":1,"start_line":152}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.files.close_source", phase="implementation-call", span={"end_byte":5292,"end_column":1,"end_line":160,"start_byte":5087,"start_column":1,"start_line":152}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Unit, path="$.return")
    _result = _cott_wrap_async_protocol(_result, Unit, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def read_span(source: LogSource, span: ByteSpan) -> bytes:
    """Toolong's get_raw: the content bytes [span.start, span.end). Empty when
start >= end. With Some(descriptor) read them with os.pread (fewer bytes
near the end of the content). With Nothing, read source.path through the
active scenario file-system fixture, decompress it as source.compression
says, and slice. Read failures give empty bytes."""
    source = _cott_normalize_f32_abi(source, LogSource, path="$.source")
    span = _cott_normalize_f32_abi(span, ByteSpan, path="$.span")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/files/read_span.py", "332b580f96bcd4ee738ffbffaa52146de84a61c4fc2a85bc0719dd670d3a4b17", "read_span", expected_project_name="toolong", expected_cott_symbol="real.toolong.files.read_span")
        _result = _implementation(source, span)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.files.read_span"
        if _error.span is None:
            _error.span = {"end_byte":5887,"end_column":1,"end_line":174,"start_byte":5292,"start_column":1,"start_line":160}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.files.read_span", phase="implementation-call", span={"end_byte":5887,"end_column":1,"end_line":174,"start_byte":5292,"start_column":1,"start_line":160}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.files.read_span", phase="implementation-call", span={"end_byte":5887,"end_column":1,"end_line":174,"start_byte":5292,"start_column":1,"start_line":160}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, bytes, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((not ((span).start >= (span).end)) or (len(_result) == 0))), "real.toolong.files.read_span", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.files.read_span", clause="ensures:1", phase="ensures", span={"end_byte":5786,"end_column":56,"end_line":169,"start_byte":5735,"start_column":5,"start_line":169}, expected="true", actual="false")
        if not (_cott_contract_condition(((((span).start >= (span).end) or (len(_result) <= ((span).end - (span).start)))), "real.toolong.files.read_span", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.files.read_span", clause="ensures:2", phase="ensures", span={"end_byte":5860,"end_column":74,"end_line":170,"start_byte":5791,"start_column":5,"start_line":170}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, bytes, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def read_lines(source: LogSource, spans: CottList[ByteSpan]) -> CottList[str]:
    """Toolong's get_line for every span, in order: the span's bytes
(real.toolong.files.read_span) decoded as UTF-8 with errors="replace",
with every leading and trailing LF and CR removed (str.strip("\\n\\r")) and
tabs expanded with str.expandtabs(4)."""
    source = _cott_normalize_f32_abi(source, LogSource, path="$.source")
    spans = _cott_normalize_f32_abi(spans, CottList[ByteSpan], path="$.spans")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/files/read_lines.py", "f397ce5368e382201caf16382e610fb59c519081f72205c6c136e8c20bca7034", "read_lines", expected_project_name="toolong", expected_cott_symbol="real.toolong.files.read_lines")
        _result = _implementation(source, spans)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.files.read_lines"
        if _error.span is None:
            _error.span = {"end_byte":6301,"end_column":1,"end_line":186,"start_byte":5887,"start_column":1,"start_line":174}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.files.read_lines", phase="implementation-call", span={"end_byte":6301,"end_column":1,"end_line":186,"start_byte":5887,"start_column":1,"start_line":174}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.files.read_lines", phase="implementation-call", span={"end_byte":6301,"end_column":1,"end_line":186,"start_byte":5887,"start_column":1,"start_line":174}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[str], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == len(spans))), "real.toolong.files.read_lines", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.files.read_lines", clause="ensures:1", phase="ensures", span={"end_byte":6274,"end_column":36,"end_line":182,"start_byte":6243,"start_column":5,"start_line":182}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def scan_breaks(source: LogSource, start: U64, end: U64) -> Opaque[Literal["file_breaks"]]:
    """The offsets of every LF byte in the content range [start, min(end,
source.size)), ascending, as an opaque tuple of U64s. Read the range in
bounded chunks with os.pread when source.descriptor is Some; with Nothing,
use the fixture content as real.toolong.files.read_span does."""
    source = _cott_normalize_f32_abi(source, LogSource, path="$.source")
    start = _cott_normalize_f32_abi(start, U64, path="$.start")
    end = _cott_normalize_f32_abi(end, U64, path="$.end")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/files/scan_breaks.py", "c9bd90448dcb5ac0f86801a0ed3ea364b0b3b7a6caa59a02287ccc175e068430", "scan_breaks", expected_project_name="toolong", expected_cott_symbol="real.toolong.files.scan_breaks")
        _result = _implementation(source, start, end)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.files.scan_breaks"
        if _error.span is None:
            _error.span = {"end_byte":6721,"end_column":1,"end_line":196,"start_byte":6301,"start_column":1,"start_line":186}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.files.scan_breaks", phase="implementation-call", span={"end_byte":6721,"end_column":1,"end_line":196,"start_byte":6301,"start_column":1,"start_line":186}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.files.scan_breaks", phase="implementation-call", span={"end_byte":6721,"end_column":1,"end_line":196,"start_byte":6301,"start_column":1,"start_line":186}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Opaque[Literal["file_breaks"]], path="$.return")
    _result = _cott_wrap_async_protocol(_result, Opaque[Literal["file_breaks"]], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def poll_source(source: LogSource, position: U64) -> TailChunk:
    """One poll of Toolong's tail watcher: read up to 65536 bytes of content
starting at position (os.pread with a descriptor; the fixture content
otherwise). The result position is position plus the number of bytes read
and breaks are the offsets (position + index) of the LF bytes read, in
order. Nothing read gives position unchanged and no breaks. Content that
shrank below position (truncation) is not detected, exactly as upstream."""
    source = _cott_normalize_f32_abi(source, LogSource, path="$.source")
    position = _cott_normalize_f32_abi(position, U64, path="$.position")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/files/poll_source.py", "c997820d7f87c4cdf062e30550170dfc0edd08985a793619e54b5188fd598e4e", "poll_source", expected_project_name="toolong", expected_cott_symbol="real.toolong.files.poll_source")
        _result = _implementation(source, position)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.files.poll_source"
        if _error.span is None:
            _error.span = {"end_byte":7326,"end_column":1,"end_line":210,"start_byte":6721,"start_column":1,"start_line":196}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.files.poll_source", phase="implementation-call", span={"end_byte":7326,"end_column":1,"end_line":210,"start_byte":6721,"start_column":1,"start_line":196}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.files.poll_source", phase="implementation-call", span={"end_byte":7326,"end_column":1,"end_line":210,"start_byte":6721,"start_column":1,"start_line":196}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TailChunk, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).position >= position)), "real.toolong.files.poll_source", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.files.poll_source", clause="ensures:1", phase="ensures", span={"end_byte":7299,"end_column":40,"end_line":206,"start_byte":7264,"start_column":5,"start_line":206}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TailChunk, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def scan_timestamps(source: LogSource, position: U64, first_line: U64, limit: U64, order: CottList[U8]) -> TimestampBatch:
    """One batch of Toolong's merge scan. Starting at position, read up to limit
lines the way a binary readline does: a line is the bytes up to and
including the next LF, or the remaining bytes when no LF follows; reading
stops at the end of the content (source.size). Each line, decoded as UTF-8
with errors="replace" and still ending with its LF, is scanned with
real.toolong.timestamps.scan_timestamp using the current order, which
carries over from line to line. Entry k has line first_line + k, end the
offset just after the line, and seconds
real.toolong.timestamps.timestamp_seconds of the timestamp found or 0.0.
The result position is the offset after the last line read and order is
the final order. Return entries as an opaque tuple of TimestampEntry so
a 10000-line batch is safe across the facade boundary."""
    source = _cott_normalize_f32_abi(source, LogSource, path="$.source")
    position = _cott_normalize_f32_abi(position, U64, path="$.position")
    first_line = _cott_normalize_f32_abi(first_line, U64, path="$.first_line")
    limit = _cott_normalize_f32_abi(limit, U64, path="$.limit")
    order = _cott_normalize_f32_abi(order, CottList[U8], path="$.order")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/files/scan_timestamps.py", "626764a096835245bef835014d0404f78b12d370ba98875c565afe45bec64dbd", "scan_timestamps", expected_project_name="toolong", expected_cott_symbol="real.toolong.files.scan_timestamps")
        _result = _implementation(source, position, first_line, limit, order)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.files.scan_timestamps"
        if _error.span is None:
            _error.span = {"end_byte":8416,"end_column":1,"end_line":236,"start_byte":7326,"start_column":1,"start_line":210}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.files.scan_timestamps", phase="implementation-call", span={"end_byte":8416,"end_column":1,"end_line":236,"start_byte":7326,"start_column":1,"start_line":210}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.files.scan_timestamps", phase="implementation-call", span={"end_byte":8416,"end_column":1,"end_line":236,"start_byte":7326,"start_column":1,"start_line":210}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TimestampBatch, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((_result).position >= position)), "real.toolong.files.scan_timestamps", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.files.scan_timestamps", clause="ensures:1", phase="ensures", span={"end_byte":8389,"end_column":40,"end_line":232,"start_byte":8354,"start_column":5,"start_line":232}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TimestampBatch, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def find_line(sources: CottList[LogSource], index: TabIndex, line_count: U64, start: I64, direction: I8, query: FindQuery) -> FindResult:
    """Toolong's advance_search while the find dialog is shown. Examine lines
start, start + 1, ..., line_count - 1 when direction is positive, or start,
start - 1, ..., 0 when it is not (no lines when start is negative or, going
forward, not below line_count). For each line, locate it with
real.toolong.index.line_location, read its raw bytes with
real.toolong.files.read_span from sources[location.file] (an empty string
when that file is missing), decode them as UTF-8 with errors="replace"
without stripping anything (so lines after the first of a single file
start with the preceding LF), and test them with
real.toolong.text.line_matches. The first line that matches is the result
line; invalid_regex is true when that test reported an invalid regular
expression."""
    sources = _cott_normalize_f32_abi(sources, CottList[LogSource], path="$.sources")
    index = _cott_normalize_f32_abi(index, TabIndex, path="$.index")
    line_count = _cott_normalize_f32_abi(line_count, U64, path="$.line_count")
    start = _cott_normalize_f32_abi(start, I64, path="$.start")
    direction = _cott_normalize_f32_abi(direction, I8, path="$.direction")
    query = _cott_normalize_f32_abi(query, FindQuery, path="$.query")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/files/find_line.py", "657ede7be7916f1f98be69d1043265520797a9a95b154bc929287a73ae02d47f", "find_line", expected_project_name="toolong", expected_cott_symbol="real.toolong.files.find_line")
        _result = _implementation(sources, index, line_count, start, direction, query)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.files.find_line"
        if _error.span is None:
            _error.span = {"end_byte":9573,"end_column":1,"end_line":264,"start_byte":8416,"start_column":1,"start_line":236}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.files.find_line", phase="implementation-call", span={"end_byte":9573,"end_column":1,"end_line":264,"start_byte":8416,"start_column":1,"start_line":236}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.files.find_line", phase="implementation-call", span={"end_byte":9573,"end_column":1,"end_line":264,"start_byte":8416,"start_column":1,"start_line":236}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, FindResult, path="$.return")
    if _cott_test_context:
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = (_result).line
            if type(_cott_match_value) is Some and True:
                found = _cott_match_value.value
                return (_cott_contract_condition(((found < line_count)), "real.toolong.files.find_line", "ensures:1"))
            _cott_contract_condition((False), "real.toolong.files.find_line", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.files.find_line", clause="ensures:1", phase="ensures", span={"end_byte":9481,"end_column":73,"end_line":259,"start_byte":9413,"start_column":5,"start_line":259}, expected="true", actual="false")
        def _cott_match_ensures_2() -> bool:
            _cott_match_value = (_result).line
            if type(_cott_match_value) is Some and True:
                found = _cott_match_value.value
                return (_cott_contract_condition(((start >= 0)), "real.toolong.files.find_line", "ensures:2"))
            _cott_contract_condition((False), "real.toolong.files.find_line", "ensures:2:applicable")
            return True
        if not (_cott_match_ensures_2()):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.files.find_line", clause="ensures:2", phase="ensures", span={"end_byte":9546,"end_column":65,"end_line":260,"start_byte":9486,"start_column":5,"start_line":260}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, FindResult, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def line_timestamp(sources: CottList[LogSource], index: TabIndex, line: U64, orders: CottList[CottList[U8]]) -> TimestampAt:
    """Toolong's get_timestamp: locate line with real.toolong.index.line_location,
read its text as real.toolong.files.read_lines does from
sources[location.file] (the empty string when that file is missing) and
scan it with real.toolong.timestamps.scan_timestamp using that file's
order. orders holds one order per file; before scanning, missing entries up
to the file's index are filled with
real.toolong.timestamps.default_timestamp_order(). The result orders are
the (filled) orders with that file's order replaced by the scan's order."""
    sources = _cott_normalize_f32_abi(sources, CottList[LogSource], path="$.sources")
    index = _cott_normalize_f32_abi(index, TabIndex, path="$.index")
    line = _cott_normalize_f32_abi(line, U64, path="$.line")
    orders = _cott_normalize_f32_abi(orders, CottList[CottList[U8]], path="$.orders")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/files/line_timestamp.py", "63f664d831451209f4870b629fd21e0cfea520eb7241c1f26f0edcd439044daf", "line_timestamp", expected_project_name="toolong", expected_cott_symbol="real.toolong.files.line_timestamp")
        _result = _implementation(sources, index, line, orders)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.files.line_timestamp"
        if _error.span is None:
            _error.span = {"end_byte":10360,"end_column":1,"end_line":285,"start_byte":9573,"start_column":1,"start_line":264}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.files.line_timestamp", phase="implementation-call", span={"end_byte":10360,"end_column":1,"end_line":285,"start_byte":9573,"start_column":1,"start_line":264}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.files.line_timestamp", phase="implementation-call", span={"end_byte":10360,"end_column":1,"end_line":285,"start_byte":9573,"start_column":1,"start_line":264}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TimestampAt, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len((_result).orders) >= len(orders))), "real.toolong.files.line_timestamp", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.files.line_timestamp", clause="ensures:1", phase="ensures", span={"end_byte":10333,"end_column":44,"end_line":281,"start_byte":10294,"start_column":5,"start_line":281}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TimestampAt, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def locate_time(sources: CottList[LogSource], index: TabIndex, line_count: U64, from_line: U64, steps: I32, unit: TimeUnit, orders: CottList[CottList[U8]]) -> TimeJump:
    """Toolong's timestamp navigation (keys m/M, h/H, d/D) from from_line, using
real.toolong.files.line_timestamp for every timestamp read and threading
the orders through all reads.

Starting at line = from_line, while the line has no timestamp: advance line
by one and count the step; when the count reaches line_count or exceeds 10,
the result line is Nothing (bell). With the timestamp t found, let
direction be +1 when steps > 0 and -1 otherwise, move line by direction,
and compute the target real.toolong.timestamps.shift_timestamp(t, steps,
unit) (Nothing: the result line is Nothing).

Forward: while line < line_count, stop at the first line whose timestamp
compares (real.toolong.timestamps.compare_timestamps) greater than or equal
to the target; otherwise advance. Backward: while line > 0, stop at the
first line whose timestamp compares less than or equal to the target;
otherwise go back one line. Incomparable timestamps (naive against aware)
never stop the walk. The result line is where the walk stopped (possibly
line_count or 0)."""
    sources = _cott_normalize_f32_abi(sources, CottList[LogSource], path="$.sources")
    index = _cott_normalize_f32_abi(index, TabIndex, path="$.index")
    line_count = _cott_normalize_f32_abi(line_count, U64, path="$.line_count")
    from_line = _cott_normalize_f32_abi(from_line, U64, path="$.from_line")
    steps = _cott_normalize_f32_abi(steps, I32, path="$.steps")
    unit = _cott_normalize_f32_abi(unit, TimeUnit, path="$.unit")
    orders = _cott_normalize_f32_abi(orders, CottList[CottList[U8]], path="$.orders")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/files/locate_time.py", "b1af573e4e41ee1e0af34eb4fbd1b323884609222145ce08fbbc9ce7cdef2ace", "locate_time", expected_project_name="toolong", expected_cott_symbol="real.toolong.files.locate_time")
        _result = _implementation(sources, index, line_count, from_line, steps, unit, orders)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.files.locate_time"
        if _error.span is None:
            _error.span = {"end_byte":11785,"end_column":1,"end_line":319,"start_byte":10360,"start_column":1,"start_line":285}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.files.locate_time", phase="implementation-call", span={"end_byte":11785,"end_column":1,"end_line":319,"start_byte":10360,"start_column":1,"start_line":285}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.files.locate_time", phase="implementation-call", span={"end_byte":11785,"end_column":1,"end_line":319,"start_byte":10360,"start_column":1,"start_line":285}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, TimeJump, path="$.return")
    if _cott_test_context:
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = (_result).line
            if type(_cott_match_value) is Some and True:
                found = _cott_match_value.value
                return (_cott_contract_condition(((found <= line_count)), "real.toolong.files.locate_time", "ensures:1"))
            _cott_contract_condition((False), "real.toolong.files.locate_time", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.files.locate_time", clause="ensures:1", phase="ensures", span={"end_byte":11758,"end_column":74,"end_line":315,"start_byte":11689,"start_column":5,"start_line":315}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, TimeJump, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def save_lines(sources: CottList[LogSource], index: TabIndex, line_count: U64, path: Path) -> Result[U64, SaveError]:
    """Toolong's save of a merged view (--output-merge): for each line 0 ..
line_count - 1 in order, read its text as real.toolong.files.read_lines
does (locating it with real.toolong.index.line_location; missing files
give ""), and write every non-empty line followed by LF, UTF-8 encoded, to
path, replacing any existing file. Outside a Cott scenario write with the
host file system (open(path, "w", encoding="utf-8")); while a scenario
file-system fixture is active write through the fixture instead. Ok holds
the number of lines written. Any failure is SaveError.WriteFailed with
str() of the exception (of the adapter's OSError cause for fixture
failures)."""
    sources = _cott_normalize_f32_abi(sources, CottList[LogSource], path="$.sources")
    index = _cott_normalize_f32_abi(index, TabIndex, path="$.index")
    line_count = _cott_normalize_f32_abi(line_count, U64, path="$.line_count")
    path = _cott_normalize_f32_abi(path, Path, path="$.path")
    if _cott_test_context:
        _expected_error = None
        _expected_error_span = None
        _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/files/save_lines.py", "a66356344ac044c835457e5a0b132fa96fbe81646285a1b7428241acfa49f442", "save_lines", expected_project_name="toolong", expected_cott_symbol="real.toolong.files.save_lines")
        _result = _implementation(sources, index, line_count, path)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.files.save_lines"
        if _error.span is None:
            _error.span = {"end_byte":12760,"end_column":1,"end_line":344,"start_byte":11785,"start_column":1,"start_line":319}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.files.save_lines", phase="implementation-call", span={"end_byte":12760,"end_column":1,"end_line":344,"start_byte":11785,"start_column":1,"start_line":319}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.files.save_lines", phase="implementation-call", span={"end_byte":12760,"end_column":1,"end_line":344,"start_byte":11785,"start_column":1,"start_line":319}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, Result[U64, SaveError], path="$.return")
    if _cott_test_context:
        if type(_result) is Err:
            if _expected_error is not None:
                if type(_result.error) is not _expected_error:
                    raise CottContractViolation("conditional error clause failed", symbol="real.toolong.files.save_lines", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
            elif type(_result.error) not in (SaveError_WriteFailed,):
                raise CottContractViolation("returned error is not allowed", symbol="real.toolong.files.save_lines", phase="error", span={"end_byte":12760,"end_column":1,"end_line":344,"start_byte":11785,"start_column":1,"start_line":319}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
        elif _expected_error is not None:
            raise CottContractViolation("expected conditional error was not returned", symbol="real.toolong.files.save_lines", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
        if _expected_error_clause is not None:
            _cott_contract_condition(True, "real.toolong.files.save_lines", _expected_error_clause)
        if type(_result) is Err and type(_result.error) is SaveError_WriteFailed:
            _cott_contract_condition(True, "real.toolong.files.save_lines", "error:2")
        def _cott_match_ensures_1() -> bool:
            _cott_match_value = _result
            if type(_cott_match_value) is Ok and True:
                written = _cott_match_value.value
                return (_cott_contract_condition(((written <= line_count)), "real.toolong.files.save_lines", "ensures:1"))
            _cott_contract_condition((False), "real.toolong.files.save_lines", "ensures:1:applicable")
            return True
        if not (_cott_match_ensures_1()):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.files.save_lines", clause="ensures:1", phase="ensures", span={"end_byte":12688,"end_column":56,"end_line":338,"start_byte":12637,"start_column":5,"start_line":338}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[U64, SaveError], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["DecompressError", "DecompressError_Corrupt", "FindResult", "SaveError", "SaveError_WriteFailed", "SourceError", "SourceError_NotFound", "SourceError_OpenFailed", "TailChunk", "TimeJump", "TimestampAt", "TimestampBatch", "close_source", "decompress", "detect_compression", "find_line", "line_timestamp", "locate_time", "open_source", "poll_source", "read_lines", "read_span", "save_lines", "scan_breaks", "scan_timestamps"]
