import socket
import ssl
from typing import Final

from cott_runtime import CottList, Err, Ok, Result
from real.posting.client_types import Header, HttpMethod, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, MAX_RESPONSE_BODY_BYTES, PostingError, PostingError_InvalidRequest, PostingError_NetworkFailed, Request, Response

_MAX_REDIRECTS: Final[int] = 10
_CHUNK: Final[int] = 65536
_MAX_HEAD: Final[int] = 1048576
_STRIPPED: Final[str] = " authorization cookie proxy-authorization host "
_TOKEN: Final[str] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!#$%&'*+-.^_`|~"
_ALPHA: Final[str] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_SCHEME_CHARS: Final[str] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-."
_URL_CHARS: Final[str] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;="
_HEX: Final[str] = "0123456789abcdefABCDEF"
_DIGITS: Final[str] = "0123456789"


def _method_name(method: HttpMethod) -> str:
    if isinstance(method, HttpMethod_Get):
        return "GET"
    if isinstance(method, HttpMethod_Head):
        return "HEAD"
    if isinstance(method, HttpMethod_Post):
        return "POST"
    if isinstance(method, HttpMethod_Put):
        return "PUT"
    if isinstance(method, HttpMethod_Patch):
        return "PATCH"
    if isinstance(method, HttpMethod_Delete):
        return "DELETE"
    if isinstance(method, HttpMethod_Options):
        return "OPTIONS"
    return method.name


def _is_token(text: str) -> bool:
    if not text:
        return False
    for ch in text:
        if ch not in _TOKEN:
            return False
    return True


def _url_chars_ok(text: str) -> bool:
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "%":
            if i + 2 >= n:
                return False
            if text[i + 1] not in _HEX or text[i + 2] not in _HEX:
                return False
            i += 3
        elif ch in _URL_CHARS:
            i += 1
        else:
            return False
    return True


def _split_ref(ref: str) -> tuple[str | None, str | None, str, str | None, str | None]:
    frag: str | None = None
    query: str | None = None
    scheme: str | None = None
    auth: str | None = None
    if "#" in ref:
        ref, frag = ref.split("#", 1)
    if "?" in ref:
        ref, query = ref.split("?", 1)
    i = ref.find(":")
    if i > 0 and ref[0] in _ALPHA:
        valid = True
        for ch in ref[:i]:
            if ch not in _SCHEME_CHARS:
                valid = False
        if valid:
            scheme = ref[:i]
            ref = ref[i + 1:]
    if ref.startswith("//"):
        rest = ref[2:]
        j = rest.find("/")
        if j < 0:
            auth = rest
            ref = ""
        else:
            auth = rest[:j]
            ref = rest[j:]
    return scheme, auth, ref, query, frag


def _authority(auth: str) -> tuple[str, int | None] | None:
    hostport = auth.rpartition("@")[2]
    port_text = ""
    if hostport.startswith("["):
        k = hostport.find("]")
        if k < 0:
            return None
        host = hostport[:k + 1]
        rest = hostport[k + 1:]
        if rest.startswith(":"):
            port_text = rest[1:]
        elif rest:
            return None
    else:
        host, _, port_text = hostport.partition(":")
        if ":" in port_text:
            return None
    if not host or host == "[]":
        return None
    if not port_text:
        return host, None
    for ch in port_text:
        if ch not in _DIGITS:
            return None
    port = int(port_text)
    if port > 65535:
        return None
    return host, port


def _default_port(scheme: str) -> int:
    return 443 if scheme == "https" else 80


def _parse_target(url: str) -> tuple[str, str, int, str, str] | None:
    scheme, auth, path, query, _ = _split_ref(url)
    if scheme not in ("http", "https") or auth is None:
        return None
    parsed = _authority(auth)
    if parsed is None:
        return None
    host, port = parsed
    default = _default_port(scheme)
    host_header = host
    if port is not None and port != default:
        host_header = f"{host}:{port}"
    target = path if path else "/"
    if query is not None:
        target = f"{target}?{query}"
    return scheme, host, port if port is not None else default, host_header, target


def _origin(url: str) -> tuple[str, str, int]:
    parsed = _parse_target(url)
    if parsed is None:
        return "", "", 0
    return parsed[0].lower(), parsed[1].lower(), parsed[2]


def _remove_dots(path: str) -> str:
    inp = path
    out: list[str] = []
    while inp:
        if inp.startswith("../"):
            inp = inp[3:]
        elif inp.startswith("./"):
            inp = inp[2:]
        elif inp.startswith("/./"):
            inp = inp[2:]
        elif inp == "/.":
            inp = "/"
        elif inp.startswith("/../"):
            inp = inp[3:]
            if out:
                out.pop()
        elif inp == "/..":
            inp = "/"
            if out:
                out.pop()
        elif inp == "." or inp == "..":
            inp = ""
        else:
            start = 1 if inp[0] == "/" else 0
            k = inp.find("/", start)
            if k < 0:
                k = len(inp)
            out.append(inp[:k])
            inp = inp[k:]
    return "".join(out)


def _resolve(base: str, ref: str) -> str:
    bscheme, bauth, bpath, bquery, _ = _split_ref(base)
    scheme, auth, path, query, frag = _split_ref(ref)
    if scheme is not None:
        tscheme = scheme
        tauth = auth
        tpath = _remove_dots(path)
        tquery = query
    else:
        tscheme = bscheme if bscheme is not None else ""
        if auth is not None:
            tauth = auth
            tpath = _remove_dots(path)
            tquery = query
        else:
            tauth = bauth
            if path == "":
                tpath = bpath
                tquery = query if query is not None else bquery
            else:
                if path.startswith("/"):
                    tpath = _remove_dots(path)
                elif bauth is not None and bpath == "":
                    tpath = _remove_dots("/" + path)
                else:
                    tpath = _remove_dots(bpath[:bpath.rfind("/") + 1] + path)
                tquery = query
    result = tscheme.lower() + ":"
    if tauth is not None:
        result += "//" + tauth
    result += tpath
    if tquery is not None:
        result += "?" + tquery
    if frag is not None:
        result += "#" + frag
    return result


def _next_url(url: str, location: str) -> str | None:
    if not _url_chars_ok(location):
        return None
    resolved = _resolve(url, location)
    if _parse_target(resolved) is None:
        return None
    if url.startswith("https://") and not resolved.startswith("https://"):
        return None
    return resolved


def _fill(sock: socket.socket, buf: bytearray) -> bool:
    data = sock.recv(_CHUNK)
    if not data:
        return False
    buf.extend(data)
    return True


def _read_head(sock: socket.socket, buf: bytearray) -> bytes:
    while True:
        idx = buf.find(b"\r\n\r\n")
        if idx >= 0:
            head = bytes(buf[:idx])
            del buf[:idx + 4]
            return head
        if len(buf) > _MAX_HEAD:
            raise ConnectionError("response header block too large")
        if not _fill(sock, buf):
            raise ConnectionError("connection closed before end of headers")


def _read_line(sock: socket.socket, buf: bytearray) -> bytes:
    while True:
        idx = buf.find(b"\r\n")
        if idx >= 0:
            line = bytes(buf[:idx])
            del buf[:idx + 2]
            return line
        if len(buf) > _MAX_HEAD:
            raise ConnectionError("chunk line too large")
        if not _fill(sock, buf):
            raise ConnectionError("connection closed inside chunked body")


def _read_length(sock: socket.socket, buf: bytearray, size: int) -> bytes:
    if size > MAX_RESPONSE_BODY_BYTES:
        raise ConnectionError("response body too large")
    while len(buf) < size:
        if not _fill(sock, buf):
            raise ConnectionError("connection closed before all Content-Length bytes")
    return bytes(buf[:size])


def _read_chunked(sock: socket.socket, buf: bytearray) -> bytes:
    out = bytearray()
    while True:
        line = _read_line(sock, buf)
        size_text = line.split(b";", 1)[0].strip().decode("latin-1")
        if not size_text:
            raise ConnectionError("bad chunk size")
        for ch in size_text:
            if ch not in _HEX:
                raise ConnectionError("bad chunk size")
        size = int(size_text, 16)
        if size == 0:
            trailer = _read_line(sock, buf)
            while trailer:
                trailer = _read_line(sock, buf)
            return bytes(out)
        if len(out) + size > MAX_RESPONSE_BODY_BYTES:
            raise ConnectionError("response body too large")
        while len(buf) < size + 2:
            if not _fill(sock, buf):
                raise ConnectionError("connection closed before terminating chunk")
        if bytes(buf[size:size + 2]) != b"\r\n":
            raise ConnectionError("bad chunk terminator")
        out.extend(buf[:size])
        del buf[:size + 2]


def _read_to_close(sock: socket.socket, buf: bytearray) -> bytes:
    while _fill(sock, buf):
        if len(buf) > MAX_RESPONSE_BODY_BYTES:
            raise ConnectionError("response body too large")
    if len(buf) > MAX_RESPONSE_BODY_BYTES:
        raise ConnectionError("response body too large")
    return bytes(buf)


def _parse_head(head: bytes) -> tuple[int, list[tuple[str, str]]]:
    lines = head.split(b"\r\n")
    status_line = lines[0].decode("latin-1")
    parts = status_line.split(" ")
    version = parts[0]
    if not version.startswith("HTTP/1.") or len(version) <= 7:
        raise ConnectionError("response does not start with an HTTP/1.x status line")
    for ch in version[7:]:
        if ch not in _DIGITS:
            raise ConnectionError("response does not start with an HTTP/1.x status line")
    if len(parts) < 2 or len(parts[1]) != 3:
        raise ConnectionError("invalid status line")
    for ch in parts[1]:
        if ch not in _DIGITS:
            raise ConnectionError("invalid status line")
    status = int(parts[1])
    if status < 100 or status > 599:
        raise ConnectionError("final status outside 100-599")
    headers: list[tuple[str, str]] = []
    for raw in lines[1:]:
        text = raw.decode("utf-8", errors="replace")
        name, sep, value = text.partition(":")
        if not sep:
            raise ConnectionError("header line without a colon")
        headers.append((name, value.strip(" \t")))
    return status, headers


def _is_chunked(headers: list[tuple[str, str]]) -> bool:
    codings: list[str] = []
    for name, value in headers:
        if name.lower() == "transfer-encoding":
            for item in value.split(","):
                if item.strip():
                    codings.append(item.strip().lower())
    return bool(codings) and codings[-1] == "chunked"


def _content_length(headers: list[tuple[str, str]]) -> int | None:
    found: int | None = None
    for name, value in headers:
        if name.lower() != "content-length":
            continue
        for item in value.split(","):
            text = item.strip()
            if not text:
                raise ConnectionError("bad Content-Length")
            for ch in text:
                if ch not in _DIGITS:
                    raise ConnectionError("bad Content-Length")
            number = int(text)
            if found is not None and found != number:
                raise ConnectionError("conflicting Content-Length")
            found = number
    return found


def _exchange(scheme: str, host: str, port: int, payload: bytes, method: str, timeout: float) -> tuple[int, list[tuple[str, str]], bytes]:
    chost = host[1:-1] if host.startswith("[") else host
    raw = socket.create_connection((chost, port), timeout)
    sock = raw
    try:
        if scheme == "https":
            sock = ssl.create_default_context().wrap_socket(raw, server_hostname=chost)
        sock.sendall(payload)
        buf = bytearray()
        status, received = _parse_head(_read_head(sock, buf))
        if method == "HEAD" or status < 200 or status in (204, 304):
            return status, received, b""
        if _is_chunked(received):
            return status, received, _read_chunked(sock, buf)
        length = _content_length(received)
        if length is not None:
            return status, received, _read_length(sock, buf, length)
        return status, received, _read_to_close(sock, buf)
    finally:
        sock.close()


def send_request(request: Request) -> Result[Response, PostingError]:
    if request.timeout_ms == 0:
        return Err(error=PostingError_InvalidRequest(message="timeout_ms must be positive"))
    url = request.url
    if not (url.startswith("http://") or url.startswith("https://")) or not _url_chars_ok(url) or _parse_target(url) is None:
        return Err(error=PostingError_InvalidRequest(message=f"invalid URL: {url!r}"))
    headers: list[tuple[str, str]] = []
    for header in request.headers:
        if not _is_token(header.name):
            return Err(error=PostingError_InvalidRequest(message=f"invalid header name: {header.name!r}"))
        if "\r" in header.value or "\n" in header.value:
            return Err(error=PostingError_InvalidRequest(message=f"invalid header value for {header.name!r}"))
        headers.append((header.name, header.value))
    method = _method_name(request.method)
    if not _is_token(method):
        return Err(error=PostingError_InvalidRequest(message=f"invalid HTTP method: {method!r}"))
    data = request.body.encode("utf-8")
    follow = isinstance(request.method, (HttpMethod_Get, HttpMethod_Head))
    timeout = request.timeout_ms / 1000
    redirects = 0
    while True:
        parsed = _parse_target(url)
        if parsed is None:
            return Err(error=PostingError_InvalidRequest(message=f"invalid URL: {url!r}"))
        scheme, host, port, host_header, target = parsed
        names = {name.lower() for name, _ in headers}
        lines = [f"{method} {target} HTTP/1.1"]
        if "host" not in names:
            lines.append(f"Host: {host_header}")
        for name, value in headers:
            lines.append(f"{name}: {value}")
        if "content-length" not in names and "transfer-encoding" not in names:
            if data:
                lines.append(f"Content-Length: {len(data)}")
            elif method in ("POST", "PUT", "PATCH"):
                lines.append("Content-Length: 0")
        payload = ("\r\n".join(lines) + "\r\n\r\n").encode("utf-8") + data
        try:
            status, received, body = _exchange(scheme, host, port, payload, method, timeout)
        except (OSError, ValueError) as exc:
            return Err(error=PostingError_NetworkFailed(message=f"network failure: {exc!r}"))
        location = next((value for name, value in received if name.lower() == "location"), None)
        if follow and status in (301, 302, 303, 307, 308) and location is not None and redirects < _MAX_REDIRECTS:
            next_url = _next_url(url, location)
            if next_url is not None:
                if _origin(next_url) != _origin(url):
                    headers = [(n, v) for n, v in headers if f" {n.lower()} " not in _STRIPPED]
                url = next_url
                redirects += 1
                continue
        return Ok(value=Response(status=status, url=url, headers=CottList(values=[Header(name=name, value=value) for name, value in received]), body=body.decode("utf-8", errors="replace")))
