def strip_front_matter(markdown: str) -> str:
    """Remove a leading YAML front matter document from Markdown."""
    if markdown.startswith("---\r\n"):
        position = 5
    elif markdown.startswith("---\n") or markdown.startswith("---\r"):
        position = 4
    else:
        return markdown

    length = len(markdown)
    while position <= length:
        line_feed = markdown.find("\n", position)
        carriage_return = markdown.find("\r", position)
        if line_feed < 0:
            line_end = carriage_return
        elif carriage_return < 0:
            line_end = line_feed
        else:
            line_end = min(line_feed, carriage_return)

        if line_end < 0:
            if length - position == 3 and (
                markdown.startswith("---", position) or markdown.startswith("...", position)
            ):
                return ""
            return markdown

        if line_end - position == 3 and (
            markdown.startswith("---", position) or markdown.startswith("...", position)
        ):
            if markdown.startswith("\r\n", line_end):
                return markdown[line_end + 2 :]
            return markdown[line_end + 1 :]

        if markdown.startswith("\r\n", line_end):
            position = line_end + 2
        else:
            position = line_end + 1

    return markdown
