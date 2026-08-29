import json

from real.posting.client_types import Header, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, RequestDocument


def export_yaml(request: RequestDocument) -> str:
    method: str = "GET"
    match request.method:
        case HttpMethod_Get():
            method = "GET"
        case HttpMethod_Post():
            method = "POST"
        case HttpMethod_Put():
            method = "PUT"
        case HttpMethod_Patch():
            method = "PATCH"
        case HttpMethod_Delete():
            method = "DELETE"
        case HttpMethod_Head():
            method = "HEAD"
        case HttpMethod_Options():
            method = "OPTIONS"

    headers: list[Header] = list(request.headers)
    lines: list[str] = [
        "name: " + json.dumps(request.name, ensure_ascii=True),
        "method: " + json.dumps(method, ensure_ascii=True),
        "url: " + json.dumps(request.url, ensure_ascii=True),
    ]
    if len(headers) == 0:
        lines.append("headers: []")
    else:
        lines.append("headers:")
        for header in headers:
            lines.append("  - name: " + json.dumps(header.name, ensure_ascii=True))
            lines.append("    value: " + json.dumps(header.value, ensure_ascii=True))
    lines.append("body: " + json.dumps(request.body, ensure_ascii=True))
    lines.append("json: true" if request.json_body else "json: false")
    return "\n".join(lines) + "\n"
