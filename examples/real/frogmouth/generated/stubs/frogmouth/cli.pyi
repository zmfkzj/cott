from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from frogmouth.cli_types import COMMAND_LINE_HELP as COMMAND_LINE_HELP, COMMAND_LINE_USAGE as COMMAND_LINE_USAGE, CommandLine as CommandLine, CommandLine_Browse as CommandLine_Browse, CommandLine_Invalid as CommandLine_Invalid, CommandLine_ShowHelp as CommandLine_ShowHelp, CommandLine_ShowVersion as CommandLine_ShowVersion
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
def parse_command_line(arguments: CottList[str], textual_version: str) -> CommandLine: ...

__all__ = ["COMMAND_LINE_HELP", "COMMAND_LINE_USAGE", "CommandLine", "CommandLine_Browse", "CommandLine_Invalid", "CommandLine_ShowHelp", "CommandLine_ShowVersion", "parse_command_line"]
