from pathlib import Path

from cott_runtime import Err, Ok, Result
from curriculum.page_build_types import BuiltPage, PageBuildError, PageBuildError_BlankTitle, PageBuildError_InvalidSlug, PageSource



def build_page(source: PageSource) -> Result[BuiltPage, PageBuildError]:
    def escape_text(value: str) -> str:
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;").replace("'", "&#39;")

    def render_html(title: str, body: str) -> str:
        html_lines: list[str] = ["<h1>" + escape_text(title) + "</h1>"]
        for line in body.splitlines():
            if line != "":
                html_lines.append("<p>" + escape_text(line) + "</p>")
        return "\n".join(html_lines)
    slug = source.slug
    segment_has_character = False
    for character in slug:
        if "a" <= character <= "z" or "0" <= character <= "9":
            segment_has_character = True
        elif character == "-" and segment_has_character:
            segment_has_character = False
        else:
            return Err(error=PageBuildError_InvalidSlug())
    if not segment_has_character:
        return Err(error=PageBuildError_InvalidSlug())
    if source.title.strip() == "":
        return Err(error=PageBuildError_BlankTitle())
    return Ok(value=BuiltPage(output_path=Path(slug) / "index.html", html=render_html(source.title, source.body)))
