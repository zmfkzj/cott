from curriculum.page_build import escape_page_text


def render_page_html(title: str, body: str) -> str:
    html_lines: list[str] = ["<h1>" + escape_page_text(title) + "</h1>"]
    for line in body.splitlines():
        if line != "":
            html_lines.append("<p>" + escape_page_text(line) + "</p>")
    return "\n".join(html_lines)
