from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.toolong.model_types import TabPlan

"""What the tl command line asks for: print help or the version (exit 0), a
usage error (exit 2), or run the viewer on the files with the merge options."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CommandLine_ShowHelp:
    __hash__ = None
    output: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CommandLine_ShowVersion:
    __hash__ = None
    output: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CommandLine_UsageError:
    __hash__ = None
    output: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CommandLine_Run:
    __hash__ = None
    files: CottList[str]
    merge: bool
    output_merge: Option[str]

CommandLine: TypeAlias = Union[CommandLine_ShowHelp, CommandLine_ShowVersion, CommandLine_UsageError, CommandLine_Run]

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
"""Toolong's UI.sort_paths: CPython sorted() of the paths using only this
less-than relation. The tokens of a path are the pieces of its last "/"
component split at ".", each converted to int when str.isdigit() and to
str.lower() otherwise. a < b when, walking the token pairs of zip(a, b) in
order, some pair has token_a < token_b (a pair mixing int and str compares
str(token_a) < str(token_b) instead) before the walk ends; when no pair
does, a < b exactly when a has fewer tokens than b. (A pair where token_a
is greater does not stop the walk.) The sort is stable."""
"""Toolong's LogScreen tabs for the files, after
real.toolong.cli.sort_paths: with merge and more than one file, one merged
tab titled with the final path components joined by " + ", holding every
path; otherwise one unmerged tab per file titled with the file argument as
given. Paths are Path(file)."""
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
__all__ = ["CommandLine", "CommandLine_Run", "CommandLine_ShowHelp", "CommandLine_ShowVersion", "CommandLine_UsageError"]
