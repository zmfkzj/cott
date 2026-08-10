from __future__ import annotations

from pathlib import Path
from typing import Literal, Never, Protocol, TypeVar

from cott_runtime import CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, Unit

from curriculum.page_build_types import BuiltPage as BuiltPage, PageBuildError as PageBuildError, PageBuildError_BlankTitle as PageBuildError_BlankTitle, PageBuildError_InvalidSlug as PageBuildError_InvalidSlug, PageSource as PageSource
"""Escape text for safe inclusion in generated page HTML.

Ampersands, angle brackets, and both quote characters are replaced with
their HTML character references. All other characters are preserved."""
def escape_page_text(value: str) -> str: ...

"""Render a page title and body as deterministic HTML.

The escaped title becomes one `h1`. Every nonempty body line becomes one
escaped `p` in source order; empty lines are omitted."""
def render_page_html(title: str, body: str) -> str: ...

"""Validate a page source and build its output path and HTML.

The slug must contain lowercase ASCII letters or digits in nonempty
segments separated by single hyphens. Slug validation precedes title
validation. A title containing only Unicode whitespace is rejected, while
accepted text is preserved. The output path is `<slug>/index.html`, and
`render_page_html` produces the page content."""
def build_page(source: PageSource) -> Result[BuiltPage, PageBuildError]: ...

__all__ = ["BuiltPage", "PageBuildError", "PageBuildError_BlankTitle", "PageBuildError_InvalidSlug", "PageSource", "build_page", "escape_page_text", "render_page_html"]
