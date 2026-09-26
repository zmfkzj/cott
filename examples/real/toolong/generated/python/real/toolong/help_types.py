from __future__ import annotations

from collections.abc import Generator, Iterator
import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Final, ForwardRef, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottContractViolation, CottExternal, CottList, CottSet, Dyn, Err, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Nothing, Ok, Opaque, Option, Result, Some, U8, U16, U32, U64, UNIT, Unit, _cott_descending_by, _cott_ends_with, _cott_euclidean_mod, _cott_normalize_f32, _cott_starts_with, _cott_unique_by, _cott_validate_abi, _cott_validated_construction
from cott_runtime import _cott_contract_condition
from real.toolong.model_types import StyledText

"""Toolong's help text (help.py HELP_MD), rendered below the title in the help
screen."""
HELP_MARKDOWN: Final[str] = "\nTooLong is a log file viewer / navigator for the terminal.\n\nBuilt with [Textual](https://www.textualize.io/)\n\nRepository: [https://github.com/Textualize/toolong](https://github.com/Textualize/toolong) Author: [Will McGugan](https://www.willmcgugan.com)\n\n---\n\n### Navigation\n\n- `tab` / `shift+tab` to navigate between widgets.\n- `home` / `end` Jump to start or end of file. Press `end` a second time to *tail* the current file.\n- `page up` / `page down` to go to the next / previous page.\n- `↑` / `↓` Move up / down a line.\n- `m` / `M` Advance +1 / -1 minutes.\n- `h` / `H` Advance +1 / -1 hours.\n- `d` / `D` Advance +1 / -1 days.\n- `enter` Toggle pointer mode.\n- `escape` Dismiss.\n\n### Other keys\n\n- `ctrl+f` or `/` Show find dialog.\n- `ctrl+l` Toggle line numbers.\n- `ctrl+t` Tail current file.\n- `ctrl+c` Exit the app.\n\n### Opening Files\n\nOpen files from the command line.\n\n```bash\n$ tl foo.log bar.log\n```\n\nIf you specify more than one file, they will be displayed within tabs.\n\n#### Opening compressed files\n\nIf a file is compressed with BZip or GZip, it will be uncompressed automatically:\n\n```bash\n$ tl foo.log.2.gz\n```\n\n#### Merging files\n\nMultiple files will open in tabs. \nIf you add the `--merge` switch, TooLong will merge all the log files based on their timestamps:\n\n```bash\n$ tl mysite.log* --merge\n```\n\n### Pointer mode\n\nPointer mode lets you navigate by line.\nTo enter pointer mode, press `enter` or click a line. \nWhen in pointer mode, the navigation keys will move this pointer rather than scroll the log file.\n\nPress `enter` again or click the line a second time to expand the line in to a new panel.\n\nPress `escape` to hide the line panel if it is visible, or to leave pointer mode if the line panel is not visible.\n\n\n### Credits\n\nInspiration and regexes taken from [LogMerger](https://github.com/ptmcg/logmerger) by Paul McGuire.\n\n\n### License\n\nCopyright 2024 Will McGugan\n\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:\n\nThe above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.\n\nTHE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n\n"

"""Toolong's help screen title art (help.py TITLE for version 1.4.0)."""
HELP_TITLE: Final[str] = "\n _______          _                       \n|__   __|        | |    Built with Textual\n   | | ___   ___ | |     ___  _ __   __ _ \n   | |/ _ \\ / _ \\| |    / _ \\| '_ \\ / _` |\n   | | (_) | (_) | |___| (_) | | | | (_| |\n   |_|\\___/ \\___/|______\\___/|_| |_|\\__, |\n                                     __/ |\n   Moving at Terminal velocity      |___/  v1.4.0\n\n"

"""The help screen's rainbow title, centered in a content area width cells
wide. The lines are HELP_TITLE.splitlines() (ten lines, the first and last
empty). Line i is colored with the i-th color of
#881177, #aa3355, #cc6666, #ee9944, #eedd00, #99dd55, #44dd88, #22ccbb,
#00bbcc, #0099cc, #3366bb, #663399 (the span's style code is "fg:" + that
color). The title
block is as wide as its widest line (49 cells) and is indented by
max(0, width - 49) // 2 spaces: a non-empty line becomes that many spaces
followed by the line, with one span over the line part; an empty line
stays "" with no spans."""
"""HELP_MARKDOWN rendered for a content area width cells wide, with a
two-cell margin on each side: rich 13.7.0 Markdown(HELP_MARKDOWN) rendered
by a Console(width=max(1, width - 4), color_system="truecolor",
force_terminal=True, file=io.StringIO()) with render_lines(..., pad=False).
Each rendered line becomes a StyledText whose text is two spaces followed
by the line's segment texts with trailing spaces removed, and whose spans
are the non-null segment styles converted like
real.toolong.text.decode_ansi converts rich styles (offsets shifted by the
two-space margin, clipped to the kept text, empty spans dropped). The
result wraps (cott_runtime.Opaque with tag "toolong.help-markdown") a
Python tuple of those real.toolong.model.StyledText values in line order;
it is opaque because the styled document exceeds the facade traversal
bound."""
__all__ = ["HELP_MARKDOWN", "HELP_TITLE"]
