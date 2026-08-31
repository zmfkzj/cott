from real.posting.client_types import Response


def render_response(response: Response) -> str:
    header_lines = "".join(
        f"{header.name}: {header.value}\n" for header in response.headers
    )
    return f"{response.status} {response.url}\n{header_lines}\n{response.body}"
