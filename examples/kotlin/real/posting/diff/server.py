#!/usr/bin/env python3
"""Loopback HTTP fixture servers for the posting differential harness.

Raw-socket HTTP/1.1, one request per connection, always ``Connection: close``.  Every response byte is chosen by
the route: no ``Date``/``Server`` header, a fixed header order, and deliberately hostile framing (dropped
connections, truncated bodies, chunked and close-delimited bodies, out-of-range statuses, 64 MiB bodies).

The request target is split at the first "?" only (never through ``urllib``), and every request line is logged,
so a client that sends a space, a fragment or a normalized path is visible.

Routing ignores the directory prefix of the request path: only the LAST path segment names the route and every
parameter comes from the query string.  ``/dir/sub/redir?to=../echo`` therefore exercises relative-Location
resolution.  Two request headers override the routing (a case sets them; the client passes them on unchanged):

  X-Echo: 1                  a path whose last segment names no route (or is empty) answers like ``echo``
  X-Mirror: ref=REF          "redirect once": the first request per ``X-Mirror-Id`` whose path equals
    X-Mirror-Id: ID          ``X-Mirror-At`` (default /b/c/d;p) answers 302 with ``Location: REF``; every later
    X-Mirror-At: PATH        request that carries the header, wherever it goes, answers like ``echo``.  All of
                             these responses carry ``X-Target: <request target as received>``.  The state is
                             cleared between the Python and the Kotlin half (``Fixtures.reset_stats``).

Routes (all methods are accepted everywhere):

  text                       200 "hello world"
  unicode                    200 UTF-8 text with accents, CJK and an emoji
  empty                      200, empty body
  index                      (the empty last segment) 200 "index"
  status?code=NNN            status NNN (verbatim in the status line); 204/304 carry no body
  binary?hex=HEX             200 with the raw bytes HEX
  charset?cs=NAME            200, UTF-8 bytes, Content-Type charset=NAME (must be ignored)
  headers                    200 with duplicate/mixed-case/empty response headers in a fixed order
  echo                       200 JSON: method, version, target, body, selected request headers (+ their order)
  redir?status=S&to=LOC      status S with Location LOC (``to_hex=HEX`` sends raw bytes, ``nolocation=1`` omits
                             it, ``dup=LOC2`` adds a second Location header); without ``to``/``to_hex`` it
                             behaves like ``echo``
  chain?n=K                  K>0: 302 to /chain?n=K-1; K=0: 200 "end"
  loop                       302 to itself
  x-out                      302 to the peer server's /echo (cross-origin)
  x-bounce                   302 to the peer server's /x-out (cross-origin, then back)
  drop                       read the request, close without answering
  drop-after-status          send the status line only, close
  drop-mid-headers           close after half a header line
  drop-before-body           complete headers announcing 5 body bytes, close
  drop-mid-body              Content-Length 1000, 12 body bytes, close
  drop-mid-chunk             chunked body: one whole chunk, then close (no terminating chunk)
  drop-inside-chunk          chunked body: a chunk announces 16 bytes, 3 arrive, close
  drop-mid-terminator        chunked body: whole chunk, "0\\r\\n", close (terminating chunk incomplete)
  garbage                    not HTTP at all
  status-line?hex=HEX        the raw status line HEX, then Content-Length 2 and the body "ok"
  bad-header-line            a header line without a colon between valid ones
  close-delimited            200 without Content-Length; body ends at connection close
  chunked                    200 with Transfer-Encoding: chunked
  chunk-ext                  chunked with chunk extensions and a trailer field ("wikipedia")
  chunk-bad-size             chunked with a non-hexadecimal chunk size
  interim                    a 102 interim response, then a 200 "final"
  hdr-ows                    response header values with leading/trailing spaces and tabs
  hdr-nonascii               response header values with bytes >= 0x80 (Latin-1 and UTF-8 spellings)
  slow?ms=N                  wait N ms, then 200
  drip?chunks=C&gap_ms=G     Content-Length C*10; one 10-byte piece every G ms
  big?n=N[&chunked=1][&prefix_hex=HEX][&unit_hex=HEX]
                             N body bytes: HEX (optional), then the UNIT bytes (default ``a``)
                             repeated up to N (a partial last unit is cut)
  <anything else>            404 "not found"
"""

from __future__ import annotations

import http
import json
import socket
import socketserver
import threading
import time
import urllib.parse
from collections.abc import Callable, Iterator
from dataclasses import dataclass

#: Request headers the ``echo`` route reports (lower-case names).  Everything else a client
#: sends (User-Agent, Accept, Connection, Content-Length, ...) is client-default noise.
ECHO_HEADERS = frozenset(
    {
        "authorization",
        "cookie",
        "proxy-authorization",
        "host",
        "content-type",
        "x-keep",
        "x-multi",
        "x-first",
        "x-second",
    }
)

CHUNK = 1 << 20
_NO_BODY = frozenset({204, 304})
MIRROR_DEFAULT_AT = "/b/c/d;p"


@dataclass(frozen=True)
class Req:
    method: str
    target: str  # exactly as received on the request line
    version: str
    path: str  # target before the first "?" (and before any "#")
    query: dict[str, str]
    headers: list[tuple[str, str]]
    body: bytes


class _Abort(Exception):
    """A route asked to close the connection without sending anything more."""


def _read_chunked(rfile) -> bytes:
    body = bytearray()
    while True:
        size = int(rfile.readline(65537).split(b";", 1)[0].strip() or b"0", 16)
        if size == 0:
            while rfile.readline(65537) not in (b"\r\n", b"\n", b""):
                pass
            return bytes(body)
        body += rfile.read(size)
        rfile.readline(65537)


def _read_request(rfile, sock: socket.socket, note: Callable[[str], None]) -> Req | None:
    line = rfile.readline(65537)
    if not line:
        return None
    if line[:1] == b"\x16":  # a TLS ClientHello: not HTTP, refuse fast
        note("<TLS ClientHello>")
        return None
    text = line.decode("latin-1").rstrip("\r\n")
    note(text)
    parts = text.split(" ")
    if len(parts) != 3:
        raise ValueError(f"malformed request line {line!r}")
    method, target, version = parts
    headers: list[tuple[str, str]] = []
    while True:
        raw = rfile.readline(65537)
        if raw in (b"\r\n", b"\n", b""):
            break
        name, sep, value = raw.decode("latin-1").partition(":")
        if not sep:
            raise ValueError(f"malformed header line {raw!r}")
        headers.append((name.strip(), value.strip()))
    lowered = {name.lower(): value for name, value in headers}
    if lowered.get("expect", "").lower() == "100-continue":
        sock.sendall(b"HTTP/1.1 100 Continue\r\n\r\n")
    if "chunked" in lowered.get("transfer-encoding", "").lower():
        body = _read_chunked(rfile)
    else:
        body = rfile.read(int(lowered.get("content-length", "0") or "0"))
    path, _, query_text = target.partition("?")
    path = path.split("#", 1)[0]
    query = dict(urllib.parse.parse_qsl(query_text.split("#", 1)[0], keep_blank_values=True))
    return Req(method, target, version, path, query, headers, body)


def _reason(code: str) -> str:
    try:
        return http.HTTPStatus(int(code)).phrase
    except ValueError:
        return "Status"


def _head(code: str, headers: list[tuple[str, str]]) -> bytes:
    lines = [f"HTTP/1.1 {code} {_reason(code)}"]
    lines += [f"{name}: {value}" if value else f"{name}:" for name, value in headers]
    return ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1")


class Ctx:
    """One request being answered."""

    def __init__(self, server: Server, sock: socket.socket, req: Req) -> None:
        self.server = server
        self.sock = sock
        self.req = req
        self.q = req.query
        self.is_head = req.method == "HEAD"

    def header(self, name: str) -> str | None:
        wanted = name.lower()
        return next((value for key, value in self.req.headers if key.lower() == wanted), None)

    def send(self, data: bytes | memoryview) -> None:
        self.sock.sendall(data)

    def respond(
        self,
        code: int | str,
        body: bytes = b"",
        *,
        ctype: str = "text/plain; charset=utf-8",
        extra: list[tuple[str, str]] | None = None,
    ) -> None:
        """A complete, Content-Length framed response (no body for HEAD, 204 and 304)."""
        headers = list(extra or [])
        if int(code) not in _NO_BODY:
            headers += [("Content-Type", ctype), ("Content-Length", str(len(body)))]
        headers.append(("Connection", "close"))
        self.send(_head(str(code), headers))
        if not self.is_head and int(code) not in _NO_BODY:
            self.send(body)

    def peer(self, path: str) -> str:
        return self.server.peer_origin + path


def r_text(c: Ctx) -> None:
    c.respond(200, b"hello world")


def r_unicode(c: Ctx) -> None:
    c.respond(200, "h\u00e9llo w\u00f6rld \u2014 \u65e5\u672c\u8a9e \U0001f600\n".encode())


def r_empty(c: Ctx) -> None:
    c.respond(200)


def r_status(c: Ctx) -> None:
    code = c.q.get("code", "200")
    c.respond(code, f"status {code}\n".encode())


def r_binary(c: Ctx) -> None:
    c.respond(200, bytes.fromhex(c.q.get("hex", "")))


def r_charset(c: Ctx) -> None:
    charset = c.q.get("cs", "iso-8859-1")
    c.respond(200, "h\u00e9llo \u00fcber".encode(), ctype=f"text/plain; charset={charset}")


def r_headers(c: Ctx) -> None:
    body = b"ok"
    headers = [
        ("X-Zeta", "z1"),
        ("X-Alpha", "a1"),
        ("Set-Cookie", "a=1"),
        ("X-Dup", "first"),
        ("Set-Cookie", "b=2"),
        ("x-dup", "second"),
        ("X-Empty", ""),
        ("X-Spaces", "value  with   inner  spaces"),
        ("Content-Type", "text/plain; charset=utf-8"),
        ("Content-Length", str(len(body))),
        ("Connection", "close"),
    ]
    c.send(_head("200", headers))
    if not c.is_head:
        c.send(body)


def r_echo(c: Ctx, extra: list[tuple[str, str]] | None = None) -> None:
    seen: dict[str, list[str]] = {}
    order: list[str] = []
    for name, value in c.req.headers:
        lowered = name.lower()
        if lowered in ECHO_HEADERS:
            seen.setdefault(lowered, []).append(value)
            order.append(lowered)
    payload = {
        "method": c.req.method,
        "version": c.req.version,
        "target": c.req.target,
        "body": c.req.body.decode("utf-8", errors="replace"),
        "body_bytes": len(c.req.body),
        "headers": seen,
        "order": order,
        "order_no_host": [name for name in order if name != "host"],
    }
    c.respond(200, json.dumps(payload, sort_keys=True, ensure_ascii=True).encode(), ctype="application/json", extra=extra)


def r_redir(c: Ctx) -> None:
    if "to" not in c.q and "to_hex" not in c.q:
        r_echo(c)
        return
    extra: list[tuple[str, str]] = []
    if c.q.get("nolocation") != "1":
        value = bytes.fromhex(c.q["to_hex"]).decode("latin-1") if "to_hex" in c.q else c.q["to"]
        extra.append(("Location", value))
        if "dup" in c.q:
            extra.append(("Location", c.q["dup"]))
    c.respond(c.q.get("status", "302"), b"redirecting\n", extra=extra)


def r_mirror(c: Ctx) -> None:
    ref = c.header("x-mirror") or ""
    ident = c.header("x-mirror-id") or ref
    at = c.header("x-mirror-at") or MIRROR_DEFAULT_AT
    trace = [("X-Target", c.req.target)]
    if ref.startswith("ref=") and c.req.path == at and c.server.first_use(ident):
        c.respond(302, b"redirecting\n", extra=[("Location", ref[4:])] + trace)
    else:
        r_echo(c, extra=trace)


def r_chain(c: Ctx) -> None:
    remaining = int(c.q.get("n", "0"))
    if remaining <= 0:
        c.respond(200, b"end")
    else:
        c.respond(302, b"redirecting\n", extra=[("Location", f"/chain?n={remaining - 1}")])


def r_loop(c: Ctx) -> None:
    c.respond(302, b"redirecting\n", extra=[("Location", "/loop")])


def r_x_out(c: Ctx) -> None:
    c.respond(302, b"redirecting\n", extra=[("Location", c.peer("/echo"))])


def r_x_bounce(c: Ctx) -> None:
    c.respond(302, b"redirecting\n", extra=[("Location", c.peer("/x-out"))])


def r_drop(c: Ctx) -> None:
    raise _Abort


def r_drop_after_status(c: Ctx) -> None:
    c.send(b"HTTP/1.1 200 OK\r\n")
    raise _Abort


def r_drop_mid_headers(c: Ctx) -> None:
    c.send(b"HTTP/1.1 200 OK\r\nContent-Le")
    raise _Abort


def r_drop_before_body(c: Ctx) -> None:
    c.send(_head("200", [("Content-Type", "text/plain"), ("Content-Length", "5"), ("Connection", "close")]))
    raise _Abort


def r_drop_mid_body(c: Ctx) -> None:
    c.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 1000\r\nConnection: close\r\n\r\npartial-body")
    raise _Abort


_CHUNKED_HEAD = [("Content-Type", "text/plain; charset=utf-8"), ("Transfer-Encoding", "chunked"), ("Connection", "close")]


def r_drop_mid_chunk(c: Ctx) -> None:
    c.send(_head("200", _CHUNKED_HEAD))
    c.send(b"8\r\nchunk-1;\r\n")
    raise _Abort


def r_drop_inside_chunk(c: Ctx) -> None:
    c.send(_head("200", _CHUNKED_HEAD))
    c.send(b"10\r\nabc")
    raise _Abort


def r_drop_mid_terminator(c: Ctx) -> None:
    c.send(_head("200", _CHUNKED_HEAD))
    c.send(b"5\r\nhello\r\n0\r\n")
    raise _Abort


def r_garbage(c: Ctx) -> None:
    c.send(b"this is not http\r\n\r\n")
    raise _Abort


def r_status_line(c: Ctx) -> None:
    c.send(bytes.fromhex(c.q["hex"]) + b"\r\nContent-Type: text/plain\r\nContent-Length: 2\r\nConnection: close\r\n\r\n")
    if not c.is_head:
        c.send(b"ok")


def r_bad_header_line(c: Ctx) -> None:
    c.send(
        b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nthis line has no colon\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok"
    )


def r_close_delimited(c: Ctx) -> None:
    c.send(_head("200", [("Content-Type", "text/plain; charset=utf-8"), ("Connection", "close")]))
    if not c.is_head:
        c.send(b"read until close")
    raise _Abort


def r_chunked(c: Ctx) -> None:
    c.send(_head("200", _CHUNKED_HEAD))
    if c.is_head:
        return
    for piece in (b"chunk-1;", b"chunk-2;", b"chunk-3"):
        c.send(f"{len(piece):x}\r\n".encode() + piece + b"\r\n")
    c.send(b"0\r\n\r\n")


def r_chunk_ext(c: Ctx) -> None:
    c.send(_head("200", _CHUNKED_HEAD))
    if not c.is_head:
        c.send(b'4;ext=1\r\nwiki\r\n5;a=b;c="d"\r\npedia\r\n0;last\r\nX-Trailer: t\r\n\r\n')


def r_chunk_bad_size(c: Ctx) -> None:
    c.send(_head("200", _CHUNKED_HEAD))
    if not c.is_head:
        c.send(b"zz\r\nabc\r\n0\r\n\r\n")


def r_interim(c: Ctx) -> None:
    c.send(b"HTTP/1.1 102 Processing\r\nX-Interim: yes\r\n\r\n")
    c.respond(200, b"final")


def r_hdr_ows(c: Ctx) -> None:
    c.send(
        b"HTTP/1.1 200 OK\r\nX-Lead:     lead\r\nX-Trail: trail    \r\nX-Tab: \ttab\t\r\nX-Both:   both  \r\n"
        b"Content-Length: 2\r\nConnection: close\r\n\r\nok"
    )


def r_hdr_nonascii(c: Ctx) -> None:
    c.send(
        b"HTTP/1.1 200 OK\r\nX-Latin1: caf\xe9\r\nX-Utf8: caf\xc3\xa9\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok"
    )


def r_slow(c: Ctx) -> None:
    time.sleep(int(c.q.get("ms", "1000")) / 1000)
    c.respond(200, b"slow done")


def r_drip(c: Ctx) -> None:
    chunks = int(c.q.get("chunks", "4"))
    gap = int(c.q.get("gap_ms", "500")) / 1000
    c.send(
        _head(
            "200",
            [("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(chunks * 10)), ("Connection", "close")],
        )
    )
    if c.is_head:
        return
    for index in range(chunks):
        if index:
            time.sleep(gap)
        c.send(str(index % 10).encode() * 10)


def _big_pieces(total: int, prefix: bytes, unit: bytes) -> Iterator[memoryview | bytes]:
    if prefix:
        yield prefix
    step = CHUNK - CHUNK % len(unit)  # whole units per piece, so the stream is one unbroken repetition
    filler = memoryview(unit * (step // len(unit)))
    remaining = total - len(prefix)
    while remaining > 0:
        size = min(step, remaining)
        yield filler[:size]
        remaining -= size


def r_big(c: Ctx) -> None:
    total = int(c.q.get("n", "0"))
    prefix = bytes.fromhex(c.q.get("prefix_hex", ""))
    unit = bytes.fromhex(c.q.get("unit_hex", "61"))
    if c.q.get("chunked") == "1":
        c.send(_head("200", _CHUNKED_HEAD))
        if c.is_head:
            return
        for piece in _big_pieces(total, prefix, unit):
            c.send(f"{len(piece):x}\r\n".encode())
            c.send(piece)
            c.send(b"\r\n")
        c.send(b"0\r\n\r\n")
        return
    c.send(_head("200", [("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(total)), ("Connection", "close")]))
    if not c.is_head:
        for piece in _big_pieces(total, prefix, unit):
            c.send(piece)


def r_index(c: Ctx) -> None:
    c.respond(200, b"index")


def r_not_found(c: Ctx) -> None:
    c.respond(404, b"not found")


ROUTES: dict[str, Callable[[Ctx], None]] = {
    "": r_index,
    "text": r_text,
    "unicode": r_unicode,
    "empty": r_empty,
    "status": r_status,
    "binary": r_binary,
    "charset": r_charset,
    "headers": r_headers,
    "echo": r_echo,
    "redir": r_redir,
    "chain": r_chain,
    "loop": r_loop,
    "x-out": r_x_out,
    "x-bounce": r_x_bounce,
    "drop": r_drop,
    "drop-after-status": r_drop_after_status,
    "drop-mid-headers": r_drop_mid_headers,
    "drop-before-body": r_drop_before_body,
    "drop-mid-body": r_drop_mid_body,
    "drop-mid-chunk": r_drop_mid_chunk,
    "drop-inside-chunk": r_drop_inside_chunk,
    "drop-mid-terminator": r_drop_mid_terminator,
    "garbage": r_garbage,
    "status-line": r_status_line,
    "bad-header-line": r_bad_header_line,
    "close-delimited": r_close_delimited,
    "chunked": r_chunked,
    "chunk-ext": r_chunk_ext,
    "chunk-bad-size": r_chunk_bad_size,
    "interim": r_interim,
    "hdr-ows": r_hdr_ows,
    "hdr-nonascii": r_hdr_nonascii,
    "slow": r_slow,
    "drip": r_drip,
    "big": r_big,
}


def dispatch(c: Ctx) -> None:
    if c.header("x-mirror") is not None:
        r_mirror(c)
        return
    name = c.req.path.rsplit("/", 1)[-1]
    route = ROUTES.get(name)
    if (route is None or name == "") and c.header("x-echo") is not None:
        r_echo(c)
        return
    (route or r_not_found)(c)


class _Handler(socketserver.StreamRequestHandler):
    timeout = 30  # seconds for any blocking read from a client that stalls
    rbufsize = 1 << 16
    wbufsize = 0

    def handle(self) -> None:
        server: Server = self.server  # type: ignore[assignment]
        self.request.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        server.note_connection()
        try:
            req = _read_request(self.rfile, self.request, server.note_request_line)
            if req is None:
                return
            dispatch(Ctx(server, self.request, req))
        except _Abort:
            pass
        except (OSError, ValueError):  # the client went away, or sent something that is not HTTP
            pass


class Server(socketserver.ThreadingTCPServer):
    """One loopback listener that records what reaches it (every connection and every request line)."""

    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 128

    def __init__(self, name: str, host: str = "127.0.0.1", port: int = 0, family: int = socket.AF_INET) -> None:
        self.address_family = family
        super().__init__((host, port), _Handler)
        self.name = name
        self.peer_origin = ""
        self._lock = threading.Lock()
        self.connections = 0
        self.requests: list[str] = []
        self._mirrored: set[str] = set()

    @property
    def port(self) -> int:
        return self.server_address[1]

    @property
    def host(self) -> str:
        ip = self.server_address[0]
        return f"[{ip}]:{self.port}" if ":" in ip else f"{ip}:{self.port}"

    @property
    def origin(self) -> str:
        return f"http://{self.host}"

    def note_connection(self) -> None:
        with self._lock:
            self.connections += 1

    def note_request_line(self, line: str) -> None:
        with self._lock:
            self.requests.append(line)

    def first_use(self, ident: str) -> bool:
        with self._lock:
            if ident in self._mirrored:
                return False
            self._mirrored.add(ident)
            return True

    def reset_stats(self) -> None:
        with self._lock:
            self.connections = 0
            self.requests = []
            self._mirrored = set()

    def start(self) -> None:
        threading.Thread(target=self.serve_forever, name=f"fixture-{self.name}", daemon=True).start()

    def handle_error(self, request, client_address) -> None:  # noqa: ANN001 - socketserver signature
        pass


class Fixtures:
    """The servers a harness run needs.

    ``a`` and ``b`` are two independent origins (cross-origin redirects go between them); ``never`` must never be
    contacted (InvalidRequest cases point at it); ``closed`` is a port that is bound but not listening, so
    connecting to it is refused for the whole run.  Two listeners exist only where the machine allows them:
    ``v6`` on ``[::1]`` and ``d80`` on ``127.0.0.1:80`` (a privileged port: bindable inside a private network
    namespace, see run.py); ``available_tags()`` names the case tags they make runnable.
    """

    def __init__(self) -> None:
        self.unavailable: dict[str, str] = {}  # case tag -> why its listener could not be bound
        self.a = Server("a")
        self.b = Server("b")
        self.never = Server("never")
        self.v6 = self._optional("ipv6", lambda: Server("v6", "::1", 0, socket.AF_INET6), "[::1]")
        self.d80 = self._optional("port80", lambda: Server("d80", "127.0.0.1", 80), "127.0.0.1:80")
        self.a.peer_origin = self.b.origin
        self.b.peer_origin = self.a.origin
        for server in (self.never, self.v6, self.d80):
            if server is not None:
                server.peer_origin = self.a.origin
        self._closed = socket.socket()
        self._closed.bind(("127.0.0.1", 0))
        self.closed_port: int = self._closed.getsockname()[1]
        self.servers = [server for server in (self.a, self.b, self.never, self.v6, self.d80) if server is not None]
        for server in self.servers:
            server.start()

    def _optional(self, tag: str, build: Callable[[], Server], where: str) -> Server | None:
        try:
            return build()
        except OSError as error:
            self.unavailable[tag] = f"cannot bind {where}: {error.strerror or error}"
            return None

    def available_tags(self) -> set[str]:
        return ({"ipv6"} if self.v6 else set()) | ({"port80"} if self.d80 else set())

    def variables(self) -> dict[str, str]:
        variables = {
            "A": self.a.origin,
            "A_HOST": self.a.host,
            "A_PORT": str(self.a.port),
            "B": self.b.origin,
            "B_HOST": self.b.host,
            "B_PORT": str(self.b.port),
            "N": self.never.origin,
            "N_HOST": self.never.host,
            "CLOSED": f"http://127.0.0.1:{self.closed_port}",
        }
        if self.v6 is not None:
            variables.update({"V6": self.v6.origin, "V6_HOST": self.v6.host, "V6_PORT": str(self.v6.port)})
        return variables

    def reset_stats(self) -> None:
        for server in self.servers:
            server.reset_stats()

    def close(self) -> None:
        for server in self.servers:
            server.shutdown()
            server.server_close()
        self._closed.close()


if __name__ == "__main__":
    fixtures = Fixtures()
    for key, value in fixtures.variables().items():
        print(f"{{{key}}} = {value}")
    print(f"optional listeners: {sorted(fixtures.available_tags()) or 'none'}")
    print("serving; Ctrl-C to stop", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        fixtures.close()
