from pathlib import Path

from cott_runtime import Err, Ok, Result
from curriculum.page_build import render_page_html
from curriculum.page_build_types import BuiltPage, PageBuildError, PageBuildError_BlankTitle, PageBuildError_InvalidSlug, PageSource


def build_page(source: PageSource) -> Result[BuiltPage, PageBuildError]:
    slug = source.slug
    if not slug or slug[0] == "-" or slug[-1] == "-":
        return Err(error=PageBuildError_InvalidSlug())
    for character in slug:
        if not ("a" <= character <= "z" or "0" <= character <= "9" or character == "-"):
            return Err(error=PageBuildError_InvalidSlug())
    if "--" in slug:
        return Err(error=PageBuildError_InvalidSlug())

    title = source.title
    if not title or title.isspace():
        return Err(error=PageBuildError_BlankTitle())

    return Ok(value=BuiltPage(output_path=Path(slug) / "index.html", html=render_page_html(title, source.body)))
