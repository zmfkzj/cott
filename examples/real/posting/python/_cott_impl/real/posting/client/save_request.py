import json
import os
from pathlib import Path

from cott_runtime import UNIT, Err, Ok, Result, Unit
from real.posting.client_types import Header, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, PostingError, PostingError_SaveFailed, RequestDocument


def save_request(path: Path, request: RequestDocument) -> Result[Unit, PostingError]:
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
    source = "\n".join(lines) + "\n"

    parent = path.parent
    if not parent.is_dir():
        return Err(error=PostingError_SaveFailed(path=path, message="parent directory does not exist"))
    if not os.access(parent, os.W_OK | os.X_OK):
        return Err(error=PostingError_SaveFailed(path=path, message="parent directory is not writable"))
    if path.exists() and not path.is_file():
        return Err(error=PostingError_SaveFailed(path=path, message="request path is not a regular file"))
    if path.is_symlink() and not path.exists():
        return Err(error=PostingError_SaveFailed(path=path, message="request path is a dangling symbolic link"))
    if path.exists() and not os.access(path, os.W_OK):
        return Err(error=PostingError_SaveFailed(path=path, message="request document is not writable"))

    path.write_text(source, encoding="utf-8")
    return Ok(value=UNIT)
