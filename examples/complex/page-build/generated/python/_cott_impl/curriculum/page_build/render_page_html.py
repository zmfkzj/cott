from curriculum.page_build import escape_page_text


def render_page_html(title: str, body: str) -> str:
    elements: list[str] = ["<h1>" + escape_page_text(title) + "</h1>"]
    for line in body.splitlines():
        if line:
            elements.append("<p>" + escape_page_text(line) + "</p>")
    return "\n".join(elements)
