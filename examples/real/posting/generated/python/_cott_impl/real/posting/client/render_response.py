from real.posting.client_types import Response


def render_response(response: Response) -> str:
    lines: list[str] = [f"{response.status} {response.url}"]
    for header in response.headers:
        lines.append(f"{header.name}: {header.value}")
    lines.append("")
    lines.append(response.body)
    return "\n".join(lines)
