from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
"""The usage line of the command-line interface."""
COMMAND_LINE_USAGE: Final[str] = "usage: frogmouth [-h] [-v] [file ...]"

"""The complete --help text, without a trailing newline."""
COMMAND_LINE_HELP: Final[str] = "usage: frogmouth [-h] [-v] [file ...]\n\nFrogmouth -- A Markdown viewer for the terminal.\n\npositional arguments:\n  file           The Markdown file to view\n\noptions:\n  -h, --help     show this help message and exit\n  -v, --version  Show version information.\n\nv0.9.1"

"""What the command line asks for. Browse starts the browser at the joined
positional arguments, if any; ShowHelp and ShowVersion print text to
standard output and exit with status 0; Invalid prints message to standard
error and exits with status 2."""
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CommandLine_Browse:
    __hash__ = None
    address: Option[str]

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CommandLine_ShowHelp:
    __hash__ = None
    text: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CommandLine_ShowVersion:
    __hash__ = None
    text: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class CommandLine_Invalid:
    __hash__ = None
    message: str

CommandLine: TypeAlias = Union[CommandLine_Browse, CommandLine_ShowHelp, CommandLine_ShowVersion, CommandLine_Invalid]

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
__all__ = ["COMMAND_LINE_HELP", "COMMAND_LINE_USAGE", "CommandLine", "CommandLine_Browse", "CommandLine_Invalid", "CommandLine_ShowHelp", "CommandLine_ShowVersion"]
