from __future__ import annotations

from collections.abc import Generator, Iterator
import asyncio as _asyncio
import dataclasses as _dataclasses
import threading as _threading
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _CottAsyncRLock, _cott_euclidean_mod, _cott_load, _cott_normalize_f32, _cott_normalize_f32_abi, _cott_validate_abi, _cott_wrap_async_protocol
from cott_runtime import _cott_contract_condition
from cott_runtime import _cott_ends_with, _cott_starts_with

from frogmouth.cli_types import COMMAND_LINE_HELP, COMMAND_LINE_USAGE, CommandLine, CommandLine_Browse, CommandLine_Invalid, CommandLine_ShowHelp, CommandLine_ShowVersion

def parse_command_line(arguments: CottList[str], textual_version: str) -> CommandLine:
    """Interpret the command-line arguments, program name excluded, like
upstream Frogmouth's argparse parser with the options -h/--help and
-v/--version and the positional "file" arguments.

Every argument after the first argument that is exactly "--" is
positional, and that "--" itself is dropped. Before it, an argument is an
option when it starts with "-", is longer than one character, contains
no space and is not a negative number (matching ^-\\d+$ or ^-\\d*\\.\\d+$);
every other argument is positional.

The first option, from left to right, that asks for help or the version
decides the result. Help is "-h", "--" followed by a non-empty prefix of
"help", or a single-dash option whose first letter is "h"; it gives
ShowHelp(COMMAND_LINE_HELP). Version is "-v", "--" followed by a
non-empty prefix of "version", or a single-dash option whose first letter
is "v"; it gives ShowVersion of "frogmouth 0.9.1 (Textual vVERSION)"
where VERSION is textual_version.

Otherwise, when there are other options, the result is Invalid of
COMMAND_LINE_USAGE, "\\n", "frogmouth: error: unrecognized arguments: "
and those options in order separated by one space. Otherwise it is
Browse of the positional arguments joined with single spaces, or Browse
of Nothing when there are none."""
    arguments = _cott_validate_abi(arguments, CottList[str], path="$.arguments")
    textual_version = _cott_validate_abi(textual_version, str, path="$.textual_version")
    try:
        _implementation = _cott_load("_cott_impl/frogmouth/cli/parse_command_line.py", "94f2d414635fe63bb78ff2975bda56a0c7a4a47c6ad71a670fc590fd1cdb4994", "parse_command_line", expected_project_name="frogmouth", expected_cott_symbol="frogmouth.cli.parse_command_line")
        _result = _implementation(arguments, textual_version)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "frogmouth.cli.parse_command_line"
        if _error.span is None:
            _error.span = {"end_byte":2955,"end_column":1,"end_line":61,"start_byte":916,"start_column":1,"start_line":25}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="frogmouth.cli.parse_command_line", phase="implementation-call", span={"end_byte":2955,"end_column":1,"end_line":61,"start_byte":916,"start_column":1,"start_line":25}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="frogmouth.cli.parse_command_line", phase="implementation-call", span={"end_byte":2955,"end_column":1,"end_line":61,"start_byte":916,"start_column":1,"start_line":25}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = _cott_validate_abi(_result, CommandLine, path="$.return")
    def _cott_match_ensures_1() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is CommandLine_ShowHelp and True:
            text = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition(((text == COMMAND_LINE_HELP)), "frogmouth.cli.parse_command_line", "ensures:1"))
        _cott_contract_condition((False), "frogmouth.cli.parse_command_line", "ensures:1:applicable")
        return True
    if not (_cott_match_ensures_1()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.cli.parse_command_line", clause="ensures:1", phase="ensures", span={"end_byte":2445,"end_column":68,"end_line":52,"start_byte":2382,"start_column":5,"start_line":52}, expected="true", actual="false")
    def _cott_match_ensures_2() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is CommandLine_ShowHelp and True:
            return (_cott_contract_condition(((len(arguments) > 0)), "frogmouth.cli.parse_command_line", "ensures:2"))
        _cott_contract_condition((False), "frogmouth.cli.parse_command_line", "ensures:2:applicable")
        return True
    if not (_cott_match_ensures_2()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.cli.parse_command_line", clause="ensures:2", phase="ensures", span={"end_byte":2502,"end_column":57,"end_line":53,"start_byte":2450,"start_column":5,"start_line":53}, expected="true", actual="false")
    def _cott_match_ensures_3() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is CommandLine_ShowVersion and True:
            text = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition((((_cott_starts_with(text, "frogmouth 0.9.1 (Textual v") and _cott_ends_with(text, ")")) and (textual_version in text))), "frogmouth.cli.parse_command_line", "ensures:3"))
        _cott_contract_condition((False), "frogmouth.cli.parse_command_line", "ensures:3:applicable")
        return True
    if not (_cott_match_ensures_3()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.cli.parse_command_line", clause="ensures:3", phase="ensures", span={"end_byte":2658,"end_column":156,"end_line":54,"start_byte":2507,"start_column":5,"start_line":54}, expected="true", actual="false")
    def _cott_match_ensures_4() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is CommandLine_ShowVersion and True:
            return (_cott_contract_condition(((len(arguments) > 0)), "frogmouth.cli.parse_command_line", "ensures:4"))
        _cott_contract_condition((False), "frogmouth.cli.parse_command_line", "ensures:4:applicable")
        return True
    if not (_cott_match_ensures_4()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.cli.parse_command_line", clause="ensures:4", phase="ensures", span={"end_byte":2718,"end_column":60,"end_line":55,"start_byte":2663,"start_column":5,"start_line":55}, expected="true", actual="false")
    def _cott_match_ensures_5() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is CommandLine_Invalid and True:
            message = getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)
            return (_cott_contract_condition((_cott_starts_with(message, "usage: frogmouth [-h] [-v] [file ...]\nfrogmouth: error: unrecognized arguments: -")), "frogmouth.cli.parse_command_line", "ensures:5"))
        _cott_contract_condition((False), "frogmouth.cli.parse_command_line", "ensures:5:applicable")
        return True
    if not (_cott_match_ensures_5()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.cli.parse_command_line", clause="ensures:5", phase="ensures", span={"end_byte":2869,"end_column":151,"end_line":56,"start_byte":2723,"start_column":5,"start_line":56}, expected="true", actual="false")
    def _cott_match_ensures_6() -> bool:
        _cott_match_value = _result
        if type(_cott_match_value) is CommandLine_Browse and type(getattr(_cott_match_value, _dataclasses.fields(type(_cott_match_value))[0].name)) is Some and True:
            return (_cott_contract_condition(((len(arguments) > 0)), "frogmouth.cli.parse_command_line", "ensures:6"))
        _cott_contract_condition((False), "frogmouth.cli.parse_command_line", "ensures:6:applicable")
        return True
    if not (_cott_match_ensures_6()):
        raise CottContractViolation("ensures clause failed", symbol="frogmouth.cli.parse_command_line", clause="ensures:6", phase="ensures", span={"end_byte":2937,"end_column":68,"end_line":57,"start_byte":2874,"start_column":5,"start_line":57}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CommandLine, path="$.return", validator=_cott_validate_abi)
    return _result

__all__ = ["COMMAND_LINE_HELP", "COMMAND_LINE_USAGE", "CommandLine", "CommandLine_Browse", "CommandLine_Invalid", "CommandLine_ShowHelp", "CommandLine_ShowVersion", "parse_command_line"]
