from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol

from foo.bar_types import BarError, BarError_InvalidPayload, BarError_ProcessingFailed, BarError_ServiceUnavailable, BarOptions, InputPayload, MAX_PAYLOAD_SIZE, OutputPayload, PayloadFormat, PayloadFormat_Raw, PayloadFormat_Structured, PayloadFormat_Text, PayloadSize, Probability

def validate_payload(data: InputPayload) -> Result[InputPayload, BarError]:
    """Reject empty payload bytes before pure processing."""
    data = _cott_validate_abi(data, InputPayload, path="$.data")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((data).data) == 0)):
        _expected_error = BarError_InvalidPayload
        _expected_error_span = {"end_byte":1038,"end_column":58,"end_line":44,"start_byte":985,"start_column":5,"start_line":44}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/foo/bar/validate_payload.py", "d76048f2ee30a1402e9db63e058b78efbb134136c6b5c4b785d42c86ef8361b2", "validate_payload", expected_project_name="process-bar", expected_cott_symbol="foo.bar.validate_payload")
        _result = _implementation(data)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "foo.bar.validate_payload"
        if _error.span is None:
            _error.span = {"end_byte":1056,"end_column":1,"end_line":48,"start_byte":615,"start_column":1,"start_line":35}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="foo.bar.validate_payload", phase="implementation-call", span={"end_byte":1056,"end_column":1,"end_line":48,"start_byte":615,"start_column":1,"start_line":35}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="foo.bar.validate_payload", phase="implementation-call", span={"end_byte":1056,"end_column":1,"end_line":48,"start_byte":615,"start_column":1,"start_line":35}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[InputPayload, BarError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="foo.bar.validate_payload", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in ():
            raise CottContractViolation("returned error is not allowed", symbol="foo.bar.validate_payload", phase="error", span={"end_byte":1056,"end_column":1,"end_line":48,"start_byte":615,"start_column":1,"start_line":35}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="foo.bar.validate_payload", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            validated = _cott_match_value.value
            return (((validated).data == (data).data))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="foo.bar.validate_payload", clause="ensures:1", phase="ensures", span={"end_byte":829,"end_column":64,"end_line":40,"start_byte":770,"start_column":5,"start_line":40}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            validated = _cott_match_value.value
            return ((((validated).declared_size).value == ((data).declared_size).value))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="foo.bar.validate_payload", clause="ensures:2", phase="ensures", span={"end_byte":911,"end_column":82,"end_line":41,"start_byte":834,"start_column":5,"start_line":41}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            validated = _cott_match_value.value
            return (((validated).format == (data).format))
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="foo.bar.validate_payload", clause="ensures:3", phase="ensures", span={"end_byte":979,"end_column":68,"end_line":42,"start_byte":916,"start_column":5,"start_line":42}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[InputPayload, BarError], path="$.return", validator=_cott_validate_abi)
    return _result

def process_payload_bytes(data: bytes, options: BarOptions) -> Result[bytes, BarError]:
    """Perform the pure byte-processing step without changing payload bytes."""
    data = _cott_validate_abi(data, bytes, path="$.data")
    options = _cott_validate_abi(options, BarOptions, path="$.options")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    try:
        _implementation = _cott_load("_cott_impl/foo/bar/process_payload_bytes.py", "4bc96dca0473843882007f150e4b1fb3f33182feff1e797f2d50c756f5dde620", "process_payload_bytes", expected_project_name="process-bar", expected_cott_symbol="foo.bar.process_payload_bytes")
        _result = _implementation(data, options)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "foo.bar.process_payload_bytes"
        if _error.span is None:
            _error.span = {"end_byte":1384,"end_column":1,"end_line":60,"start_byte":1056,"start_column":1,"start_line":48}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="foo.bar.process_payload_bytes", phase="implementation-call", span={"end_byte":1384,"end_column":1,"end_line":60,"start_byte":1056,"start_column":1,"start_line":48}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="foo.bar.process_payload_bytes", phase="implementation-call", span={"end_byte":1384,"end_column":1,"end_line":60,"start_byte":1056,"start_column":1,"start_line":48}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[bytes, BarError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="foo.bar.process_payload_bytes", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (BarError_ServiceUnavailable, BarError_ProcessingFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="foo.bar.process_payload_bytes", phase="error", span={"end_byte":1384,"end_column":1,"end_line":60,"start_byte":1056,"start_column":1,"start_line":48}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="foo.bar.process_payload_bytes", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            processed = _cott_match_value.value
            return ((processed == data))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="foo.bar.process_payload_bytes", clause="ensures:1", phase="ensures", span={"end_byte":1291,"end_column":54,"end_line":53,"start_byte":1242,"start_column":5,"start_line":53}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[bytes, BarError], path="$.return", validator=_cott_validate_abi)
    return _result

def build_output(data: bytes, source_size: PayloadSize, format: PayloadFormat) -> OutputPayload:
    """Construct output from processed bytes and the original payload metadata."""
    data = _cott_validate_abi(data, bytes, path="$.data")
    source_size = _cott_validate_abi(source_size, PayloadSize, path="$.source_size")
    format = _cott_validate_abi(format, PayloadFormat, path="$.format")
    try:
        _implementation = _cott_load("_cott_impl/foo/bar/build_output.py", "222423a1f76b2633d6df3fe64fe10f905a19d7a8b92671db79c4241bfc66aa49", "build_output", expected_project_name="process-bar", expected_cott_symbol="foo.bar.build_output")
        _result = _implementation(data, source_size, format)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "foo.bar.build_output"
        if _error.span is None:
            _error.span = {"end_byte":1709,"end_column":1,"end_line":71,"start_byte":1384,"start_column":1,"start_line":60}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="foo.bar.build_output", phase="implementation-call", span={"end_byte":1709,"end_column":1,"end_line":71,"start_byte":1384,"start_column":1,"start_line":60}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="foo.bar.build_output", phase="implementation-call", span={"end_byte":1709,"end_column":1,"end_line":71,"start_byte":1384,"start_column":1,"start_line":60}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, OutputPayload, path="$.return")
    if not (((_result).data == data)):
        raise CottContractViolation("ensures clause failed", symbol="foo.bar.build_output", clause="ensures:1", phase="ensures", span={"end_byte":1609,"end_column":32,"end_line":65,"start_byte":1582,"start_column":5,"start_line":65}, expected="true", actual="false")
    if not ((((_result).source_size).value == (source_size).value)):
        raise CottContractViolation("ensures clause failed", symbol="foo.bar.build_output", clause="ensures:2", phase="ensures", span={"end_byte":1655,"end_column":46,"end_line":66,"start_byte":1614,"start_column":5,"start_line":66}, expected="true", actual="false")
    if not (((_result).format == format)):
        raise CottContractViolation("ensures clause failed", symbol="foo.bar.build_output", clause="ensures:3", phase="ensures", span={"end_byte":1691,"end_column":36,"end_line":67,"start_byte":1660,"start_column":5,"start_line":67}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, OutputPayload, path="$.return", validator=_cott_validate_abi)
    return _result

def process_bar(data: InputPayload, options: BarOptions) -> Result[OutputPayload, BarError]:
    """Compose validate_payload, process_payload_bytes, and build_output in that
order, propagating validation and processing errors unchanged."""
    data = _cott_validate_abi(data, InputPayload, path="$.data")
    options = _cott_validate_abi(options, BarOptions, path="$.options")
    _expected_error = None
    _expected_error_span = None
    _expected_error_clause = None
    if _expected_error is None and ((len((data).data) == 0)):
        _expected_error = BarError_InvalidPayload
        _expected_error_span = {"end_byte":2219,"end_column":58,"end_line":81,"start_byte":2166,"start_column":5,"start_line":81}
        _expected_error_clause = "error:4"
    try:
        _implementation = _cott_load("_cott_impl/foo/bar/process_bar.py", "200b9909178d7c70b055a0bf18fae4f9db5f71097f7ea39e7aa3f9e03b189420", "process_bar", expected_project_name="process-bar", expected_cott_symbol="foo.bar.process_bar")
        _result = _implementation(data, options)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "foo.bar.process_bar"
        if _error.span is None:
            _error.span = {"end_byte":2310,"end_column":1,"end_line":86,"start_byte":1709,"start_column":1,"start_line":71}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="foo.bar.process_bar", phase="implementation-call", span={"end_byte":2310,"end_column":1,"end_line":86,"start_byte":1709,"start_column":1,"start_line":71}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="foo.bar.process_bar", phase="implementation-call", span={"end_byte":2310,"end_column":1,"end_line":86,"start_byte":1709,"start_column":1,"start_line":71}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, Result[OutputPayload, BarError], path="$.return")
    if type(_result) is Err:
        if _expected_error is not None:
            if type(_result.error) is not _expected_error:
                raise CottContractViolation("conditional error clause failed", symbol="foo.bar.process_bar", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result.error).__name__)
        elif type(_result.error) not in (BarError_ServiceUnavailable, BarError_ProcessingFailed,):
            raise CottContractViolation("returned error is not allowed", symbol="foo.bar.process_bar", phase="error", span={"end_byte":2310,"end_column":1,"end_line":86,"start_byte":1709,"start_column":1,"start_line":71}, expected="declared unconditional error variant", actual=type(_result.error).__name__)
    elif _expected_error is not None:
        raise CottContractViolation("expected conditional error was not returned", symbol="foo.bar.process_bar", clause=_expected_error_clause, phase="error", span=_expected_error_span, expected=_expected_error.__name__, actual=type(_result).__name__)
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            output = _cott_match_value.value
            return (((output).data == (data).data))
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="foo.bar.process_bar", clause="ensures:1", phase="ensures", span={"end_byte":2024,"end_column":58,"end_line":77,"start_byte":1971,"start_column":5,"start_line":77}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            output = _cott_match_value.value
            return ((((output).source_size).value == ((data).declared_size).value))
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="foo.bar.process_bar", clause="ensures:2", phase="ensures", span={"end_byte":2098,"end_column":74,"end_line":78,"start_byte":2029,"start_column":5,"start_line":78}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is Ok and True:
            output = _cott_match_value.value
            return (((output).format == (data).format))
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="foo.bar.process_bar", clause="ensures:3", phase="ensures", span={"end_byte":2160,"end_column":62,"end_line":79,"start_byte":2103,"start_column":5,"start_line":79}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, Result[OutputPayload, BarError], path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["BarError", "BarError_InvalidPayload", "BarError_ProcessingFailed", "BarError_ServiceUnavailable", "BarOptions", "InputPayload", "MAX_PAYLOAD_SIZE", "OutputPayload", "PayloadFormat", "PayloadFormat_Raw", "PayloadFormat_Structured", "PayloadFormat_Text", "PayloadSize", "Probability", "build_output", "process_bar", "process_payload_bytes", "validate_payload"]
