from real.posting.client_types import Response


def render_response(response: Response) -> str:
    lines: list[str] = [f"{response.status} {response.url}"]
    for header in response.headers:
        lines.append(f"{header.name}: {header.value}")
    lines.append("")
    body = response.body.encode("utf-8", "replace").decode("utf-8", "replace")
    lines.append(body)
    return "\n".join(lines)
