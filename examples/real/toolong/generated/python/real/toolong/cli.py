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

from real.toolong.cli_types import CommandLine, CommandLine_Run, CommandLine_ShowHelp, CommandLine_ShowVersion, CommandLine_UsageError
from real.toolong.model_types import TabPlan

_cott_test_context = False

def _cott_set_test_context(active: bool) -> None:
    global _cott_test_context
    _cott_test_context = active

def help_text(program: str) -> str:
    """Exactly the help click 8.1.7 prints for Toolong 1.4.0's command on a
terminal at least 80 columns wide, without the final newline:

Usage: PROGRAM [OPTIONS] FILE1 FILE2
(blank line)
  View / tail / search log files.
(blank line)
Options:
  --version                Show the version and exit.
  -m, --merge              Merge files.
  -o, --output-merge PATH  Path to save merged file (requires -m).
  --help                   Show this message and exit.

PROGRAM is program; the descriptions start at column 27."""
    program = _cott_normalize_f32_abi(program, str, path="$.program")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/cli/help_text.py", "d21c78b36557e35206fc91ea86fd57e4014fb60d019a645315e385cb4e0c46d9", "help_text", expected_project_name="toolong", expected_cott_symbol="real.toolong.cli.help_text")
        _result = _implementation(program)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.cli.help_text"
        if _error.span is None:
            _error.span = {"end_byte":1210,"end_column":1,"end_line":39,"start_byte":461,"start_column":1,"start_line":16}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.cli.help_text", phase="implementation-call", span={"end_byte":1210,"end_column":1,"end_line":39,"start_byte":461,"start_column":1,"start_line":16}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.cli.help_text", phase="implementation-call", span={"end_byte":1210,"end_column":1,"end_line":39,"start_byte":461,"start_column":1,"start_line":16}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, str, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((_cott_starts_with(_result, "Usage: ")), "real.toolong.cli.help_text", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.cli.help_text", clause="ensures:1", phase="ensures", span={"end_byte":1129,"end_column":45,"end_line":34,"start_byte":1089,"start_column":5,"start_line":34}, expected="true", actual="false")
        if not (_cott_contract_condition((_cott_ends_with(_result, "Show this message and exit.")), "real.toolong.cli.help_text", "ensures:2")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.cli.help_text", clause="ensures:2", phase="ensures", span={"end_byte":1192,"end_column":63,"end_line":35,"start_byte":1134,"start_column":5,"start_line":35}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, str, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def parse_command_line(arguments: CottList[str], program: str) -> CommandLine:
    """Parse the tl arguments exactly as click 8.1.7 parses Toolong 1.4.0's
command: options --version (flag), -m/--merge (flag), -o/--output-merge
(one value), --help (flag), and any number of FILE arguments, options and
files interleaved in any order.

Scan the arguments left to right. "--" makes every later argument a file.
"-" and arguments not starting with "-" are files. An argument starting
with "--" is a long option, split at its first "=" into name and value:
an unknown name is the error "No such option: NAME" followed, when the
close matches click finds among "--version", "--merge", "--output-merge"
and "--help" (difflib.get_close_matches with its defaults, as click's
parser computes them) are one match, by " Did you mean MATCH?", and when
they are several by " (Possible options: A, B)" with the matches sorted; a
flag
given a value is the bare error "Option 'NAME' does not take a value.";
--output-merge takes its "=" value or else the next argument (whatever it
is), and with none left is the bare error "Option 'NAME' requires an
argument.". Any other argument starting with "-" is a cluster of short
options read character by character: -m sets merge, -o takes the rest of
the argument when non-empty or else the next argument (bare error
"Option '-o' requires an argument." when none is left), and any other
character c is the error "No such option: -c". The first error stops
parsing.

Results: an error is UsageError. For "No such option" errors the output is
"Usage: PROGRAM [OPTIONS] FILE1 FILE2", LF, "Try 'PROGRAM --help' for
help.", LF, LF, "Error: " + message; the bare errors are "Error: " +
message alone. Otherwise --version anywhere gives ShowVersion("PROGRAM,
version 1.4.0"); else --help anywhere gives
ShowHelp(real.toolong.cli.help_text(program)); else Run with the files in
order, merge, and the last -o/--output-merge value."""
    arguments = _cott_normalize_f32_abi(arguments, CottList[str], path="$.arguments")
    program = _cott_normalize_f32_abi(program, str, path="$.program")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/cli/parse_command_line.py", "d899a6839602f4c90902f0f2f7ad8f36d85972d0d063b8ee106b2aeb43103084", "parse_command_line", expected_project_name="toolong", expected_cott_symbol="real.toolong.cli.parse_command_line")
        _result = _implementation(arguments, program)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.cli.parse_command_line"
        if _error.span is None:
            _error.span = {"end_byte":3308,"end_column":1,"end_line":76,"start_byte":1210,"start_column":1,"start_line":39}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.cli.parse_command_line", phase="implementation-call", span={"end_byte":3308,"end_column":1,"end_line":76,"start_byte":1210,"start_column":1,"start_line":39}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.cli.parse_command_line", phase="implementation-call", span={"end_byte":3308,"end_column":1,"end_line":76,"start_byte":1210,"start_column":1,"start_line":39}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CommandLine, path="$.return")
    _result = _cott_wrap_async_protocol(_result, CommandLine, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def sort_paths(paths: CottList[str]) -> CottList[str]:
    """Toolong's UI.sort_paths: CPython sorted() of the paths using only this
less-than relation. The tokens of a path are the pieces of its last "/"
component split at ".", each converted to int when str.isdigit() and to
str.lower() otherwise. a < b when, walking the token pairs of zip(a, b) in
order, some pair has token_a < token_b (a pair mixing int and str compares
str(token_a) < str(token_b) instead) before the walk ends; when no pair
does, a < b exactly when a has fewer tokens than b. (A pair where token_a
is greater does not stop the walk.) The sort is stable."""
    paths = _cott_normalize_f32_abi(paths, CottList[str], path="$.paths")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/cli/sort_paths.py", "905653029f01fb92f90b0288fcf5dae75dea8abbb9886c044ac6467110f5f2f8", "sort_paths", expected_project_name="toolong", expected_cott_symbol="real.toolong.cli.sort_paths")
        _result = _implementation(paths)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.cli.sort_paths"
        if _error.span is None:
            _error.span = {"end_byte":4027,"end_column":1,"end_line":92,"start_byte":3308,"start_column":1,"start_line":76}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.cli.sort_paths", phase="implementation-call", span={"end_byte":4027,"end_column":1,"end_line":92,"start_byte":3308,"start_column":1,"start_line":76}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.cli.sort_paths", phase="implementation-call", span={"end_byte":4027,"end_column":1,"end_line":92,"start_byte":3308,"start_column":1,"start_line":76}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[str], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((len(_result) == len(paths))), "real.toolong.cli.sort_paths", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.cli.sort_paths", clause="ensures:1", phase="ensures", span={"end_byte":4009,"end_column":36,"end_line":88,"start_byte":3978,"start_column":5,"start_line":88}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[str], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def plan_tabs(files: CottList[str], merge: bool) -> CottList[TabPlan]:
    """Toolong's LogScreen tabs for the files, after
real.toolong.cli.sort_paths: with merge and more than one file, one merged
tab titled with the final path components joined by " + ", holding every
path; otherwise one unmerged tab per file titled with the file argument as
given. Paths are Path(file)."""
    files = _cott_normalize_f32_abi(files, CottList[str], path="$.files")
    merge = _cott_normalize_f32_abi(merge, bool, path="$.merge")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/cli/plan_tabs.py", "2d19b47ab170d5497f914b256b21c0da3e78d6c36e83055a441f2a448be9d585", "plan_tabs", expected_project_name="toolong", expected_cott_symbol="real.toolong.cli.plan_tabs")
        _result = _implementation(files, merge)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.cli.plan_tabs"
        if _error.span is None:
            _error.span = {"end_byte":4496,"end_column":1,"end_line":105,"start_byte":4027,"start_column":1,"start_line":92}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.cli.plan_tabs", phase="implementation-call", span={"end_byte":4496,"end_column":1,"end_line":105,"start_byte":4027,"start_column":1,"start_line":92}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.cli.plan_tabs", phase="implementation-call", span={"end_byte":4496,"end_column":1,"end_line":105,"start_byte":4027,"start_column":1,"start_line":92}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, CottList[TabPlan], path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition((((not (not merge)) or (len(_result) == len(files)))), "real.toolong.cli.plan_tabs", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.cli.plan_tabs", clause="ensures:1", phase="ensures", span={"end_byte":4478,"end_column":51,"end_line":101,"start_byte":4432,"start_column":5,"start_line":101}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, CottList[TabPlan], path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

def run_command_line(arguments: CottList[str], program: str) -> I32:
    """The tl entry point; returns the process exit status.

real.toolong.cli.parse_command_line(arguments, program): ShowHelp and
ShowVersion print their output and a newline to stdout and return 0;
UsageError prints its output and a newline to stderr and returns 2.

Run: when standard input is a terminal (sys.stdin.isatty()) and there
are no files, print the help text and a newline to stdout and return 0.
When it is a terminal, run real.toolong.tui.run_viewer with
ViewerSetup(tabs: real.toolong.cli.plan_tabs(files, merge), save_merge:
Path(output_merge) when given, pipe: Nothing), ignoring its Err and any
exception, and return 0.

Otherwise (piped input) the files and options are ignored, as upstream:
SIGINT and SIGTERM handlers write "^C" to stderr; the input is copied to a
tempfile.NamedTemporaryFile(mode="w+b", buffering=0, prefix="tl_") shown
as the only tab (title the temporary file name); the pipe descriptor is
duplicated with os.dup(0), "/dev/tty" is opened read-write and placed on
descriptor 0 with os.dup2 so the viewer reads the keyboard, and run_viewer
gets ViewerSetup(tabs: one unmerged TabPlan for the temporary file,
save_merge: Nothing, pipe: PipeFeed(duplicated descriptor, temporary
path)). Afterwards the duplicated descriptor and the temporary file are
closed (deleting it) and 0 is returned; errors and exceptions of the viewer
are ignored. When "/dev/tty" cannot be opened, "Error: " + str(exception)
is written to stderr and 1 is returned."""
    arguments = _cott_normalize_f32_abi(arguments, CottList[str], path="$.arguments")
    program = _cott_normalize_f32_abi(program, str, path="$.program")
    try:
        _implementation = _cott_load("_cott_impl/real/toolong/cli/run_command_line.py", "14aed1e63174aada6822a31b317284eb7b220571aaf9b5060202cc7db09eff26", "run_command_line", expected_project_name="toolong", expected_cott_symbol="real.toolong.cli.run_command_line")
        _result = _implementation(arguments, program)
    except CottContractViolation as _error:
        if _error.symbol is None or _error.symbol == "_cott_load":
            _error.symbol = "real.toolong.cli.run_command_line"
        if _error.span is None:
            _error.span = {"end_byte":6244,"end_column":1,"end_line":138,"start_byte":4496,"start_column":1,"start_line":105}
        raise
    except SystemExit as _error:
        raise CottContractViolation("implementation raised SystemExit", symbol="real.toolong.cli.run_command_line", phase="implementation-call", span={"end_byte":6244,"end_column":1,"end_line":138,"start_byte":4496,"start_column":1,"start_line":105}, expected="ordinary return or declared Never process.exit", actual="SystemExit") from _error
    except Exception as _error:
        raise CottContractViolation("implementation raised an undeclared exception", symbol="real.toolong.cli.run_command_line", phase="implementation-call", span={"end_byte":6244,"end_column":1,"end_line":138,"start_byte":4496,"start_column":1,"start_line":105}, expected="declared Result error or ordinary return", actual=type(_error).__name__) from _error
    _result = (_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi)(_result, I32, path="$.return")
    if _cott_test_context:
        if not (_cott_contract_condition(((_result >= 0)), "real.toolong.cli.run_command_line", "ensures:1")):
            raise CottContractViolation("ensures clause failed", symbol="real.toolong.cli.run_command_line", clause="ensures:1", phase="ensures", span={"end_byte":6177,"end_column":24,"end_line":134,"start_byte":6158,"start_column":5,"start_line":134}, expected="true", actual="false")
    _result = _cott_wrap_async_protocol(_result, I32, path="$.return", validator=(_cott_validate_abi if _cott_test_context else _cott_normalize_f32_abi))
    return _result

__all__ = ["CommandLine", "CommandLine_Run", "CommandLine_ShowHelp", "CommandLine_ShowVersion", "CommandLine_UsageError", "help_text", "parse_command_line", "plan_tabs", "run_command_line", "sort_paths"]
