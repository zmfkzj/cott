from __future__ import annotations

import dataclasses as _dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Generic, Literal, Never, Protocol, TypeAlias, TypeVar, Union, final, runtime_checkable

from cott_runtime import CottContractViolation, CottList, CottSet, CottTuple2, F32, F64, FrozenMap, I8, I16, I32, I64, JsonValue, Opaque, Option, Result, U8, U16, U32, U64, UNIT, Unit, _cott_euclidean_mod, _cott_normalize_f32, _cott_validate_abi
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PageSource:
    __hash__ = None
    slug: str
    title: str
    body: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class BuiltPage:
    __hash__ = None
    output_path: Path
    html: str

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PageBuildError_InvalidSlug:
    pass

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class PageBuildError_BlankTitle:
    pass

PageBuildError: TypeAlias = Union[PageBuildError_InvalidSlug, PageBuildError_BlankTitle]

"""Escape text for safe inclusion in generated page HTML.

Ampersands, angle brackets, and both quote characters are replaced with
their HTML character references. All other characters are preserved."""
"""Render a page title and body as deterministic HTML.

The escaped title becomes one `h1`. Every nonempty body line becomes one
escaped `p` in source order; empty lines are omitted."""
"""Validate a page source and build its output path and HTML.

The slug must contain lowercase ASCII letters or digits in nonempty
segments separated by single hyphens. Slug validation precedes title
validation. A title containing only Unicode whitespace is rejected, while
accepted text is preserved. The output path is `<slug>/index.html`, and
`render_page_html` produces the page content."""
__all__ = ["BuiltPage", "PageBuildError", "PageBuildError_BlankTitle", "PageBuildError_InvalidSlug", "PageSource"]
