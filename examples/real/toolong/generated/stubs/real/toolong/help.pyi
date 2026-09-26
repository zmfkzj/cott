from __future__ import annotations

from collections.abc import Generator, Iterator
from pathlib import Path
from typing import Any, Literal, Never, Protocol, TypeVar, final

from cott_runtime import AsyncGenerator, AsyncIterator, CottArray, CottBuffer, CottList, CottSet, Dyn, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from real.toolong.help_types import HELP_MARKDOWN as HELP_MARKDOWN, HELP_TITLE as HELP_TITLE
from real.toolong.model_types import StyledText
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
def help_title(width: U16) -> CottList[StyledText]: ...

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
def help_markdown(width: U16) -> Opaque[Literal["toolong.help-markdown"]]: ...

__all__ = ["HELP_MARKDOWN", "HELP_TITLE", "help_markdown", "help_title"]
