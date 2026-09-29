"""Cases for decisions D1-D14 of the send_request contract (the former "edge" behaviors, settled from upstream posting
2.10.0 / httpx 0.28.1 and written into client.cott).  Every case has an ``expect`` derived from the contract wording or
computed by the independent oracles in oracle.py; none is copied from an implementation's output.

  D1  several Location fields are joined with ", ": never valid, the 3xx is returned
  D2  a response to wire method HEAD, and any 204/304 response, has no body
  D3  the literal "." / ".." segments of the request path are removed (RFC 3986 5.2.4); "%2E" stays
  D4  the scheme of a Location is case-insensitive; the resolved URL has it in lower case
  D5  received header values have leading/trailing SP and HTAB removed
  D6  the values of the final response's header block decode as a whole: ASCII, else valid UTF-8, else ISO-8859-1
  D7  interim 100 and 102-199 responses are discarded; 101 is NetworkFailed
  D8  status line: HTTP/1.x SP three digits [SP reason], the reason may be empty or missing
  D9  chunk extensions are ignored; trailer fields are read and discarded
  D10 a chunk-size line is hexadecimal digits, then nothing, SP/HTAB, or optional SP/HTAB and ";extension"; else NetworkFailed
  D11 a connection closed after the last chunk but before the final empty line is NetworkFailed
  D12 ports: decimal digits (leading zeros allowed), empty = default, non-digit or > 65535 = InvalidRequest, 0 = NetworkFailed
  D13 a request header value with a character above U+007F is InvalidRequest
  D14 a received header line whose name is not one or more token characters immediately followed by ":" is NetworkFailed
"""

from __future__ import annotations

from casekit import (
    ABSENT,
    CREDS_NO_HOST,
    INVALID,
    KEPT_ALL,
    NETWORK,
    TCHAR_PUNCT,
    TCHARS,
    concrete,
    contains,
    custom,
    echo,
    enc,
    execute,
    followed_echo,
    ok,
    place,
    redir,
    resolved,
    rules,
    send,
    std_headers,
    stripped,
)
from oracle import chunk_size_line, expected_headers, host_header, origin, request_target, valid_block

X_ECHO = [("X-Echo", "1")]
TEXT = "text/plain; charset=utf-8"
CHUNKED_FIELDS = [("Content-Type", TEXT), ("Transfer-Encoding", "chunked"), ("Connection", "close")]
STATUS_LINE_FIELDS = [("Content-Type", "text/plain"), ("Content-Length", "2"), ("Connection", "close")]


def fields(pairs):
    return [{"name": name, "value": value} for name, value in pairs]


def canonical(text):
    """The form a case text takes in a result: this run's origins turned back into placeholders."""
    return place(concrete(text))


def headers_of(*lines: bytes):
    return {"value.headers": expected_headers(list(lines))}


# ---- D1 ---------------------------------------------------------------------------------------------------------


def group_d1():
    rules("D1")
    note = "several Location fields: the value is all of them joined with \", \", which contains a space, so it is never valid and the 3xx is returned"

    def case(ident, values, *, names=None, method="Get", status=302, first_hex=False):
        parts = []
        for index, value in enumerate(values):
            parts.append("to_hex=" + value.encode("latin-1").hex() if index == 0 and first_hex else f"{('to', 'dup', 'dup2')[index]}={enc(value)}")
        if names:
            parts.append(f"dupname={names}")
        url = f"{{A}}/redir?status={status}&" + "&".join(parts)
        locations = [("Location" if index != 1 or not names else names, value) for index, value in enumerate(values)]
        expect = {**ok(status=status, url=canonical(url), body="" if method == "Head" else "redirecting\n"),
                  "value.headers": std_headers(12, first=[(name, canonical(value)) for name, value in locations])}
        send(f"send_request/location-fields-{ident}", method, url, headers=X_ECHO, expect=expect, note=note)

    case("two-valid-not-followed", ["/echo", "/text"])
    case("three-not-followed", ["/echo", "/text", "/empty"])
    case("two-identical-not-followed", ["/echo", "/echo"])
    case("second-empty-not-followed", ["/echo", ""])
    case("first-empty-not-followed", ["", "/echo"])
    case("first-invalid-not-followed", ["/e cho", "/text"], first_hex=True)
    case("name-case-differs-not-followed", ["/echo", "/text"], names="location")
    case("cross-origin-valid-not-followed", ["{B}/echo", "{B}/echo"])
    case("head-not-followed", ["/echo", "/text"], method="Head")
    for status in (301, 303, 307, 308):
        case(f"two-valid-status-{status}-not-followed", ["/echo", "/text"], status=status)
    followed_echo("send_request/location-single-value-with-comma-is-followed", redir("/redir", "/echo,x"), "/echo,x",
                  note="one Location field whose value holds a comma is not several fields: it is resolved as it is (a comma is a URL character)")


# ---- D2 ---------------------------------------------------------------------------------------------------------


def group_d2():
    rules("D2")
    head = custom("HEAD")
    note = "the wire method is exactly HEAD: the announced Content-Length / Transfer-Encoding / connection close do not make a body"
    send("send_request/head-custom-head-method-has-no-body", head, "{A}/text", timeout=1500,
         expect={**ok(status=200, url="{A}/text", body=""), "value.headers": std_headers(11)}, note=note)
    send("send_request/head-custom-head-chunked-has-no-body", head, "{A}/chunked",
         expect={**ok(status=200, body=""), "value.headers": fields(CHUNKED_FIELDS)}, note=note)
    send("send_request/head-custom-head-close-delimited-has-no-body", head, "{A}/close-delimited",
         expect={**ok(status=200, body=""), "value.headers": fields([("Content-Type", TEXT), ("Connection", "close")])}, note=note)
    send("send_request/head-custom-head-status-404-has-no-body", head, "{A}/status?code=404", expect=ok(status=404, body=""), note=note)
    url = "{A}/redir?status=302&to=/text"
    send("send_request/head-custom-head-redirect-not-followed", head, url,
         expect={**ok(status=302, url=url, body=""), "value.headers": std_headers(12, first=[("Location", "/text")])},
         note="a Custom method never follows redirects, HEAD included")
    for label, name in (("lowercase", "head"), ("titlecase", "Head"), ("mixed-case", "hEAD")):
        send(f"send_request/head-custom-{label}-is-not-head-and-has-a-body", custom(name), "{A}/text",
             expect={**ok(status=200, body="hello world"), "value.headers": std_headers(11)},
             note="a Custom name is sent unchanged; only the wire method exactly HEAD has a body-less response")
    for code in (204, 304):
        for framing, wire, announced in (("content-length", "cl", [("Content-Length", "5")]), ("chunked", "te", [("Transfer-Encoding", "chunked")])):
            url = f"{{A}}/nobody?code={code}&framing={wire}"
            expect = {**ok(status=code, url=url, body=""), "value.headers": fields(announced + [("Connection", "close")])}
            send(f"send_request/nobody-{code}-with-{framing}", url=url, expect=expect,
                 note=f"a {code} response has no body whatever its framing headers announce (the server closes right after the headers)")
    url = "{A}/nobody?code=204&framing=cl"
    send("send_request/nobody-204-post", "Post", url, body="x", expect={**ok(status=204, url=url, body=""), "value.headers": fields([("Content-Length", "5"), ("Connection", "close")])},
         note="the 204/304 rule does not depend on the method")
    url = "{A}/nobody?code=304&framing=cl"
    send("send_request/nobody-304-head", "Head", url, expect={**ok(status=304, url=url, body=""), "value.headers": fields([("Content-Length", "5"), ("Connection", "close")])})
    final = "{A}/nobody?code=204&framing=cl"
    send("send_request/nobody-204-after-redirect", url=redir("/redir", "/nobody?code=204&framing=cl"),
         expect={**ok(status=204, url=final, body=""), "value.headers": fields([("Content-Length", "5"), ("Connection", "close")])})


# ---- D3 ---------------------------------------------------------------------------------------------------------


def group_d3():
    rules("D3")
    note = "the literal . and .. path segments are removed as in RFC 3986 5.2.4 before the request target is sent; %2E stays; Response.url is the URL as given"
    for ident, path, target in [
        ("current-segment", "/./echo", "/echo"), ("parent-at-root", "/../echo", "/echo"), ("parent-after-segment", "/a/../echo", "/echo"),
        ("contract-example", "/a/./b/../echo", "/a/echo"), ("trailing-parent", "/a/b/..", "/a/"), ("trailing-current", "/a/b/.", "/a/b/"),
        ("trailing-parent-slash", "/a/b/../", "/a/"), ("trailing-current-slash", "/a/b/./", "/a/b/"), ("only-parent", "/..", "/"),
        ("only-current", "/.", "/"), ("segment-then-parent", "/a/..", "/"), ("parents-beyond-root", "/a/../..", "/"),
        ("parents-beyond-root-then-segment", "/../../a/echo", "/a/echo"), ("three-parents", "/a/b/../../../echo", "/echo"),
        ("two-parents", "/a/b/c/../../echo", "/a/echo"), ("empty-segment-then-parent", "/a//../echo", "/a/echo"),
        ("empty-segments-are-not-dots", "/a//b/echo", "/a//b/echo"), ("three-dots-is-a-segment", "/a/.../echo", "/a/.../echo"),
        ("dot-prefixed-segment", "/a/.b/echo", "/a/.b/echo"), ("dot-suffixed-segment", "/a/b./echo", "/a/b./echo"),
        ("dotdot-prefixed-segment", "/a/..b/echo", "/a/..b/echo"), ("dotdot-suffixed-segment", "/a/b../echo", "/a/b../echo"),
        ("dot-with-parameter", "/a/.;x/echo", "/a/.;x/echo"), ("dotdot-with-parameter", "/a/..;x/echo", "/a/..;x/echo"),
        ("encoded-dotdot-upper", "/a/%2E%2E/echo", "/a/%2E%2E/echo"), ("encoded-dotdot-lower", "/a/%2e%2e/echo", "/a/%2e%2e/echo"),
        ("encoded-dot", "/a/%2e/echo", "/a/%2e/echo"), ("encoded-second-dot", "/a/.%2e/echo", "/a/.%2e/echo"),
        ("encoded-first-dot", "/a/%2e./echo", "/a/%2e./echo"), ("encoded-dotdot-after-literal-parent", "/a/b/../%2E%2E/echo", "/a/%2E%2E/echo"),
        ("encoded-slash-around-dots", "/a%2F..%2Fecho", "/a%2F..%2Fecho"), ("query-and-fragment-untouched", "/a/../echo?x=/../y#/../z", "/echo?x=/../y"),
        ("dots-in-query-only", "/echo?../..", "/echo?../.."), ("root-parent-with-query", "/..?x=1", "/?x=1"),
    ]:
        url = "{A}" + path
        assert request_target(concrete(url)) == target, (url, request_target(concrete(url)), target)
        send(f"send_request/target-dots-{ident}", url=url, headers=X_ECHO, expect=echo(target=target, url=url), note=note)
    url = "{A}?/./x"
    send("send_request/target-dots-in-query-after-empty-path", url=url, headers=X_ECHO, expect=echo(target="/?/./x", url=url), note=note)
    url = "{A}/a/../echo"
    send("send_request/target-dots-post-body", "Post", url, body="x", expect=echo(method="POST", target="/echo", body="x", url=url), note=note)
    url = "{A}/a/../redir?status=302&to=/echo"
    send("send_request/target-dots-then-redirect", url=url, headers=X_ECHO, expect=echo(target="/echo", url="{A}/echo"),
         note="the redirect is answered for the normalized path and its Location is resolved as usual; the final URL is the resolved one")


# ---- D4 ---------------------------------------------------------------------------------------------------------


def group_d4():
    rules("D4")
    note = "the scheme of a Location is case-insensitive; the resolved URL (next request, Response.url, origin comparison) has it in lower case"
    for ident, scheme in (("uppercase", "HTTP"), ("titlecase", "Http"), ("alternating", "hTTp")):
        ref = f"{scheme}://{{A_HOST}}/echo"
        followed_echo(f"send_request/location-scheme-{ident}-followed", redir("/redir", ref), ref, note=note)

    def to(ident, base, ref, headers=(), **kw):
        url = f"{base}/redir?status=302&to={enc(ref)}"
        final, target = resolved(url, ref)
        host = canonical(host_header(concrete(final)))
        same = origin(concrete(url)) == origin(concrete(final))
        expected = ({**KEPT_ALL, "host": [host]} if same else stripped(host)) if headers else {"host": [host]}
        send(f"send_request/location-scheme-{ident}", url=url, headers=list(headers) + X_ECHO,
             expect=echo(url=final, target=request_target(concrete(final)), hdr=expected), note=note, **kw)

    to("uppercase-same-origin-keeps-headers", "{A}", "HTTP://{A_HOST}/echo", CREDS_NO_HOST)
    to("uppercase-scheme-and-host-other-origin-strips-headers", "{A}", "HTTP://LOCALHOST:{A_PORT}/echo", CREDS_NO_HOST)
    to("uppercase-with-dots-query-and-fragment", "{A}", "HTTP://{A_HOST}/a/../echo?x=1#frag")
    to("uppercase-userinfo-kept-in-url", "{A}", "HTTP://u:p@{A_HOST}/echo", CREDS_NO_HOST)
    to("uppercase-from-other-origin", "{B}", "HTTP://{A_HOST}/echo", CREDS_NO_HOST)
    for label, scheme in (("uppercase", "HTTPS"), ("titlecase", "Https")):
        url = f"{{A}}/redir?status=302&to={enc(scheme + '://{A_HOST}/text')}"
        send(f"send_request/location-scheme-{label}-https-is-followed", url=url, expect=NETWORK,
             note="an https Location is followed whatever its case (http -> https is not a downgrade); the handshake with a plain listener fails")
    for ident, ref in (("uppercase-without-authority", "HTTP:g"), ("uppercase-without-host", "HTTP://"), ("uppercase-single-slash", "hTTp:/g"),
                       ("uppercase-ftp", "FTP://{A_HOST}/x"), ("uppercase-other-scheme", "HTTPX://{A_HOST}/x")):
        url = f"{{A}}/redir?status=302&to={enc(ref)}"
        send(f"send_request/location-scheme-{ident}-not-followed", url=url, headers=X_ECHO,
             expect={**ok(status=302, url=canonical(url), body="redirecting\n"), "value.headers": std_headers(12, first=[("Location", canonical(ref))])},
             note="a Location that does not resolve to an http(s) URL with a host is not followed, however its scheme is spelled")


# ---- D5 and D6: the received header fields ---------------------------------------------------------------------------

FRAMING = [b"Content-Length: 2", b"Connection: close"]


def raw_block(ident, lines, *, framing=FRAMING, rule, note=None):
    """A 200 answered by hdr-raw with exactly these header lines (plus framing): Ok with the oracle's reading of the block, or
    NetworkFailed when one of the lines is not a field line (D14)."""
    lines = list(lines) + list(framing)
    url = "{A}/hdr-raw?hex=" + b"".join(line + b"\r\n" for line in lines).hex()
    expect = {**ok(status=200, url=url, body="ok"), **headers_of(*lines)} if valid_block(lines) else NETWORK
    send(f"send_request/{ident}", url=url, expect=expect, rule=rule, note=note)


def group_d5():
    rules("D5")
    note = "received header values have leading and trailing SP and HTAB removed; names are kept as received"
    raw_block("response-header-values-trimmed-spaces", [b"X-Lead:     lead", b"X-Trail: trail    ", b"X-Both:   both  "], rule="D5", note=note)
    raw_block("response-header-values-trimmed-tabs", [b"X-Tab: \ttab\t", b"X-Tabs:\t\t\ttabs\t\t"], rule="D5", note=note)
    raw_block("response-header-values-trimmed-mixed", [b"X-Mix: \t \tmix \t \t"], rule="D5", note=note)
    raw_block("response-header-values-inner-whitespace-kept", [b"X-Inner: a \t b", b"X-Inner2:  a  b  "], rule="D5", note=note)
    raw_block("response-header-value-only-spaces-is-empty", [b"X-Blank:      "], rule="D5", note=note)
    raw_block("response-header-value-only-tabs-is-empty", [b"X-Blank:\t\t\t"], rule="D5", note=note)
    raw_block("response-header-value-only-mixed-whitespace-is-empty", [b"X-Blank: \t \t "], rule="D5", note=note)
    raw_block("response-header-value-no-space-after-colon", [b"X-Tight:v"], rule="D5", note=note)
    raw_block("response-header-value-empty", [b"X-Empty:"], rule="D5", note=note)
    raw_block("response-header-duplicates-trimmed-separately", [b"X-Dup:  first ", b"X-Dup:\tsecond\t", b"X-Dup:   "], rule="D5", note=note)
    raw_block("response-header-name-case-kept-value-trimmed", [b"x-LoWeR:  v ", b"X-UPPER:\tV\t"], rule="D5", note=note)
    raw_block("response-header-only-sp-and-htab-are-removed-utf8-nbsp", [b"X-Nb: \xc2\xa0v\xc2\xa0 "], rule="D5",
              note="U+00A0 is not SP or HTAB: it stays (here as UTF-8)")
    raw_block("response-header-only-sp-and-htab-are-removed-latin1-nbsp", [b"X-Nb: \xa0v\xa0 "], rule="D5",
              note="U+00A0 is not SP or HTAB: it stays (here as ISO-8859-1)")
    raw_block("response-header-content-length-with-outer-whitespace-frames-the-body", [b"X-Pad: 1"], framing=[b"Content-Length:   2   ", b"Connection: close"], rule="D5",
              note="the framing header is a received header value too: its whitespace is not part of the length")
    url = "{A}/redir?status=302&to=%20%20/echo%20"
    send("send_request/location-value-with-outer-whitespace-is-followed", url=url, headers=X_ECHO, rule="D5", expect=echo(target="/echo", url="{A}/echo"),
         note="the Location field value is the received value without its leading and trailing SP/HTAB, so it is the valid URL /echo")
    url = "{A}/redir?status=302&to=%09/echo%09"
    send("send_request/location-value-with-outer-tabs-is-followed", url=url, headers=X_ECHO, rule="D5", expect=echo(target="/echo", url="{A}/echo"), note="the same with HTAB")


def group_d6():
    rules("D6")
    note = "the values of the header block of the final response are decoded as a whole: every value ASCII -> as is; else every value valid UTF-8 -> UTF-8; else every value ISO-8859-1"
    raw_block("response-header-block-all-ascii", [b"X-A: a", b"X-B: b"], rule="D6", note=note)
    raw_block("response-header-block-all-utf8-value", [b"X-Utf8: caf\xc3\xa9"], rule="D6", note=note)
    raw_block("response-header-block-all-utf8-four-byte-and-cjk", [b"X-E: \xf0\x9f\x98\x80", b"X-J: \xe6\x97\xa5\xe6\x9c\xac", b"X-A: plain"], rule="D6", note=note)
    raw_block("response-header-block-latin1-value-only", [b"X-Latin1: caf\xe9"], rule="D6", note=note)
    raw_block("response-header-block-mixed-latin1-and-utf8-decodes-all-as-latin1", [b"X-Latin1: caf\xe9", b"X-Utf8: caf\xc3\xa9"], rule="D6",
              note=note + " (the UTF-8 value therefore shows as cafA-tilde-copyright)")
    raw_block("response-header-block-lone-continuation-byte", [b"X-C: a\x80b", b"X-Ok: caf\xc3\xa9"], rule="D6", note=note)
    raw_block("response-header-block-overlong-sequence", [b"X-O: \xc0\xaf"], rule="D6", note=note)
    raw_block("response-header-block-utf8-encoded-surrogate-is-not-utf8", [b"X-S: \xed\xa0\x80"], rule="D6", note=note)
    raw_block("response-header-block-above-u10ffff-is-not-utf8", [b"X-H: \xf4\x90\x80\x80"], rule="D6", note=note)
    raw_block("response-header-block-truncated-sequence-at-end-of-value", [b"X-T: ab\xe2\x82", b"X-Ok: caf\xc3\xa9"], rule="D6", note=note)
    raw_block("response-header-block-duplicate-names-decoded-alike", [b"X-D: caf\xc3\xa9", b"X-D: caf\xe9"], rule="D6", note=note)
    # only the final response's block counts
    lines = [b"X-Utf8: caf\xc3\xa9"] + FRAMING
    final = "/hdr-raw?hex=" + b"".join(line + b"\r\n" for line in lines).hex()
    send("send_request/response-header-block-only-the-final-response-counts", url="{A}/hdr-redirect?to=" + enc(final), rule="D6",
         expect={**ok(status=200, url="{A}" + final, body="ok"), **headers_of(*lines)},
         note="the redirect response carries an ISO-8859-1 header (X-First: caf\\xe9); the final response is all valid UTF-8, so it decodes as UTF-8")
    send("send_request/response-header-block-interim-headers-do-not-count", url="{A}/interim?codes=102&ihex=" + b"X-I: caf\xe9\r\n".hex(), rule="D6",
         expect={**ok(status=200, url="{A}/interim?codes=102&ihex=" + b"X-I: caf\xe9\r\n".hex(), body="final"), "value.headers": std_headers(5)},
         note="an interim response is discarded with its headers: its ISO-8859-1 byte does not change how the final (ASCII) block is read")


# ---- D7 ---------------------------------------------------------------------------------------------------------


def group_d7():
    rules("D7")
    final_headers = std_headers(5)

    def passes(ident, codes, method="Get", ihex="", headers=(), note=None):
        url = f"{{A}}/interim?codes={codes}" + (f"&ihex={ihex}" if ihex else "")
        send(f"send_request/interim-{ident}", method, url, headers=headers,
             expect={**ok(status=200, url=url, body="" if method == "Head" else "final"), "value.headers": final_headers},
             note=note or "an interim response (100, 102-199) is read with its headers and discarded; the next response is returned")

    def fails(ident, codes, drop=False, ihex="", note=None):
        url = f"{{A}}/interim?codes={codes}" + (f"&ihex={ihex}" if ihex else "") + ("&drop=1" if drop else "")
        send(f"send_request/interim-{ident}", url=url, expect=NETWORK, note=note)

    passes("102-then-final", "102")
    passes("100-then-final", "100")
    passes("103-then-final", "103")
    passes("199-then-final", "199")
    passes("100-and-103-then-final", "100,103")
    passes("six-then-final", "100,102,103,104,105,199")
    passes("head-request", "102", method="Head")
    url = "{A}/interim?codes=102"
    send("send_request/interim-after-a-followed-redirect", url=redir("/redir", "/interim?codes=102"),
         expect={**ok(status=200, url=url, body="final"), "value.headers": final_headers})
    send("send_request/interim-100-continue-then-final", "Post", "{A}/echo", [("Expect", "100-continue")], "hello",
         expect=echo(method="POST", body="hello", body_bytes=5), note="the server answers 100 Continue before reading the body; only the final response counts")
    fails("101-is-network-failed", "101", note="a 101 is NetworkFailed: no protocol upgrade is ever requested (a final 200 follows, and must not be reached)")
    fails("101-with-upgrade-headers-is-network-failed", "101", ihex=b"Upgrade: websocket\r\nConnection: Upgrade\r\n".hex())
    fails("102-then-101-is-network-failed", "102,101")
    fails("101-then-102-is-network-failed", "101,102")
    fails("then-connection-closed-is-network-failed", "102", drop=True, note="no final response ever arrives")
    fails("several-then-connection-closed-is-network-failed", "100,102,103", drop=True)


# ---- D8 ---------------------------------------------------------------------------------------------------------


def group_d8():
    rules("D8")
    accept = "the status line is HTTP/1.x, a space, three digits, optionally a space and a reason phrase that may be empty; a missing reason is accepted"
    reject = "not HTTP/1.x SP three digits [SP reason]: NetworkFailed"

    def line(ident, raw: bytes, status=None):
        url = "{A}/status-line?hex=" + raw.hex()
        expect = NETWORK if status is None else {**ok(status=status, url=url, body="ok"), "value.headers": fields(STATUS_LINE_FIELDS)}
        send(f"send_request/status-line-{'accepted' if status else 'rejected'}-{ident}", url=url, expect=expect, note=accept if status else reject)

    line("http-1-1-without-reason", b"HTTP/1.1 200", 200)
    line("http-1-1-empty-reason-after-space", b"HTTP/1.1 200 ", 200)
    line("http-1-0-without-reason", b"HTTP/1.0 200", 200)
    line("http-1-0-empty-reason-after-space", b"HTTP/1.0 200 ", 200)
    line("http-1-1-with-reason", b"HTTP/1.1 200 OK", 200)
    line("http-1-1-404-without-reason", b"HTTP/1.1 404", 404)
    line("http-1-1-599-without-reason", b"HTTP/1.1 599", 599)
    line("reason-with-inner-spaces", b"HTTP/1.1 200 A Reason  With   Spaces", 200)
    line("reason-with-colon", b"HTTP/1.1 200 OK: yes", 200)
    line("reason-that-looks-like-a-status", b"HTTP/1.1 200 404 Not Found", 200)
    line("no-space-before-reason", b"HTTP/1.1 200OK")
    line("two-spaces-before-status", b"HTTP/1.1  200 OK")
    line("tab-instead-of-space-before-reason", b"HTTP/1.1 200\tOK")
    line("tab-instead-of-space-before-status", b"HTTP/1.1\t200 OK")
    line("no-status", b"HTTP/1.1")
    line("no-status-after-space", b"HTTP/1.1 ")
    line("lower-case-http", b"http/1.1 200 OK")
    line("no-minor-version", b"HTTP/1 200 OK")
    line("leading-space", b" HTTP/1.1 200 OK")
    line("four-digit-status", b"HTTP/1.1 2000")
    line("leading-zero-four-digit-status", b"HTTP/1.1 0200 OK")
    line("plus-sign-status", b"HTTP/1.1 +200 OK")
    line("two-digit-status-without-reason", b"HTTP/1.1 20")


# ---- D9, D10, D11 -----------------------------------------------------------------------------------------------


def chunked(ident, raw: bytes, body=None, *, rule, note=None):
    """A 200 with Transfer-Encoding: chunked whose body bytes are exactly ``raw``; ``body`` None means NetworkFailed."""
    url = "{A}/chunk-raw?hex=" + raw.hex()
    expect = NETWORK if body is None else {**ok(status=200, url=url, body=body), "value.headers": fields(CHUNKED_FIELDS)}
    send(f"send_request/{ident}", url=url, expect=expect, rule=rule, note=note)


def group_d9():
    rules("D9")
    ext = "chunk extensions are ignored"
    tr = "trailer fields are read and discarded: they are not part of Response.headers"
    chunked("chunked-extensions-and-trailer", b'4;ext=1\r\nwiki\r\n5;a=b;c="d"\r\npedia\r\n0;last\r\nX-Trailer: t\r\n\r\n', "wikipedia", rule="D9", note=ext + "; " + tr)
    chunked("chunked-extension-without-value", b"4;ext\r\nwiki\r\n0\r\n\r\n", "wiki", rule="D9", note=ext)
    chunked("chunked-extension-quoted-string", b'4;a="b c"\r\nwiki\r\n0\r\n\r\n', "wiki", rule="D9", note=ext)
    chunked("chunked-extensions-several", b'4;a=1;b=2;c;d="x"\r\nwiki\r\n0\r\n\r\n', "wiki", rule="D9", note=ext)
    chunked("chunked-extension-on-last-chunk-only", b"4\r\nwiki\r\n0;done=1\r\n\r\n", "wiki", rule="D9", note=ext)
    chunked("chunked-trailer-field-not-in-headers", b"4\r\nwiki\r\n0\r\nX-Trailer: t\r\n\r\n", "wiki", rule="D9", note=tr)
    chunked("chunked-trailer-fields-several", b"4\r\nwiki\r\n0\r\nX-A: 1\r\nX-B: 2\r\nX-C: 3\r\n\r\n", "wiki", rule="D9", note=tr)
    chunked("chunked-trailer-only-empty-body", b"0\r\nX-A: 1\r\n\r\n", "", rule="D9", note=tr)
    chunked("chunked-trailer-does-not-replace-a-header", b"4\r\nwiki\r\n0\r\nContent-Type: evil\r\nX-Extra: 1\r\n\r\n", "wiki", rule="D9", note=tr + " (a trailer named like a header does not replace or add to it)")
    data = b"a\r\nb\r\nc"
    chunked("chunked-data-contains-crlf", f"{len(data):x}\r\n".encode() + data + b"\r\n0\r\n\r\n", data.decode(), rule="D9", note="chunk data is counted, never scanned")
    chunked("chunked-data-looks-like-the-end", b"5\r\n0\r\n\r\n\r\n0\r\n\r\n", "0\r\n\r\n", rule="D9", note="chunk data that spells the terminator is data")
    chunked("chunked-size-digits-any-case", b"A\r\n" + b"a" * 10 + b"\r\na\r\n" + b"b" * 10 + b"\r\n1A\r\n" + b"c" * 26 + b"\r\n1a\r\n" + b"d" * 26 + b"\r\n0\r\n\r\n",
            "a" * 10 + "b" * 10 + "c" * 26 + "d" * 26, rule="D9", note="hexadecimal digits in either case")
    chunked("chunked-size-leading-zeros", b"0003\r\nabc\r\n0000\r\n\r\n", "abc", rule="D9", note="leading zeros are hexadecimal digits too; 0000 is the last chunk")
    chunked("chunked-many-small-chunks", b"".join(b"1\r\n" + bytes([97 + index % 26]) + b"\r\n" for index in range(200)) + b"0\r\n\r\n",
            "".join(chr(97 + index % 26) for index in range(200)), rule="D9")
    chunked("chunked-empty-body-complete", b"0\r\n\r\n", "", rule="D9", note="the last chunk and the final empty line: a complete, empty body")


def sized(ident, size: bytes, data: bytes, note):
    """One chunk of ``data`` announced by the size line ``size``, then the last chunk: NetworkFailed when the oracle rejects the
    line, else Ok (the value of the line is then the length of the data, so that only a wrong reading of the line shows)."""
    value = chunk_size_line(size)
    assert value in (None, len(data)), ident
    chunked(ident, size + b"\r\n" + data + b"\r\n0\r\n\r\n", None if value is None else data.decode(), rule="D10", note=note)


def group_d10():
    rules("D10")
    grammar = "a chunk-size line is one or more hexadecimal digits, then nothing, SP/HTAB, or optional SP/HTAB and \";\" with an ignored extension"
    bad = grammar + "; anything else is NetworkFailed (the data is as long as a lenient parser would read, so accepting the line would show)"
    for ident, size, length in [
        ("letters", b"zz", 3), ("empty-size", b"", 3), ("plus-sign", b"+3", 3), ("minus-sign", b"-3", 3), ("hex-prefix", b"0x3", 3),
        ("leading-space", b" 3", 3), ("underscore-separator", b"3_0", 48), ("trailing-letter", b"3g", 3), ("decimal-point", b"3.0", 3),
        ("fullwidth-digit-utf8", "\uff13".encode(), 3), ("leading-tab", b"\t3", 3), ("just-a-semicolon", b";x=1", 3),
    ]:
        sized(f"chunked-size-not-hexadecimal-{ident}", size, b"a" * length, bad)
    for ident, size in [
        ("space-on-both-sides", b" 3 "), ("space-then-letter", b"3 x"), ("space-then-digit", b"3 3"), ("trailing-vertical-tab", b"3\x0b"),
        ("trailing-form-feed", b"3\x0c"), ("trailing-nul", b"3\x00"), ("trailing-no-break-space-utf8", b"3\xc2\xa0"),
    ]:
        sized(f"chunked-size-line-rejected-{ident}", size, b"a" * 3, bad)
    for ident, size in [
        ("trailing-space", b"2 "), ("trailing-tab", b"2\t"), ("trailing-spaces-and-tabs", b"2 \t  \t"), ("extension", b"2;a=b"), ("extension-without-value", b"2;a"),
        ("space-before-extension", b"2 ; a=b"), ("tab-before-extension", b"2\t;a=b"), ("space-after-semicolon", b"2; a=b"),
        ("leading-zeros-and-trailing-space", b"002 "),
    ]:
        sized(f"chunked-size-line-accepted-{ident}", size, b"ok", grammar)
    for ident, line in [
        ("trailing-space", b"0 "), ("trailing-tab", b"0\t"), ("space-before-extension", b"0 ;done=1"),
        ("leading-space", b" 0"), ("hex-prefix", b"0x0"), ("trailing-letter", b"0g"), ("plus-sign", b"+0"),
    ]:
        value = chunk_size_line(line)
        assert value in (0, None), ident
        chunked(f"chunked-last-chunk-line-{'rejected' if value is None else 'accepted'}-{ident}", b"2\r\nok\r\n" + line + b"\r\n\r\n", None if value is None else "ok",
                rule="D10", note="the same size-line rule for the last chunk: " + grammar)
    chunked("chunked-last-chunk-line-accepted-trailing-space-then-trailer", b"2\r\nok\r\n0 \r\nX-T: 1\r\n\r\n", "ok", rule="D10", note=grammar)
    for ident, size in [("2-pow-31-minus-1", b"7FFFFFFF"), ("2-pow-32-minus-1", b"FFFFFFFF"), ("2-pow-64-minus-1", b"FFFFFFFFFFFFFFFF"),
                        ("21-digits", b"1" + b"0" * 20), ("40-digits", b"F" * 40)]:
        chunked(f"chunked-size-beyond-the-body-limit-{ident}", size + b"\r\nabc\r\n0\r\n\r\n", rule="D10",
                note="a valid hexadecimal size far beyond what arrives (and beyond the body limit): the response cannot be completed")


def group_d11():
    rules("D11")
    note = "a connection closed after the last chunk (size 0) but before the final empty line is NetworkFailed"
    for ident, tail in [("after-last-chunk-line", b"0\r\n"), ("after-last-chunk-size-without-crlf", b"0"), ("after-last-chunk-cr-only", b"0\r"),
                        ("inside-trailer-line", b"0\r\nX-T: 1"), ("after-trailer-line", b"0\r\nX-T: 1\r\n"), ("after-several-trailer-lines", b"0\r\nX-A: 1\r\nX-B: 2\r\n")]:
        chunked(f"chunked-closed-{ident}", b"5\r\nhello\r\n" + tail, rule="D11", note=note)
    chunked("chunked-closed-after-last-chunk-with-extension", b"5\r\nhello\r\n0;done=1\r\n", rule="D11", note=note)
    chunked("chunked-closed-after-last-chunk-without-any-data", b"0\r\n", rule="D11", note=note)


# ---- D12 --------------------------------------------------------------------------------------------------------


def direct(ident, url, *, tags=(), headers=X_ECHO, note=None):
    """A request that succeeds against the echo route: Host and target come from the oracle, Response.url is the URL as given."""
    host = canonical(host_header(concrete(url)))
    send(f"send_request/{ident}", url=url, headers=headers, tags=tags,
         expect=echo(host=host, target=request_target(concrete(url)), url=canonical(url), hdr={"authorization": ABSENT}), note=note)


def redirect_to(ident, base, ref, headers=CREDS_NO_HOST, *, tags=(), note=None):
    """A followed redirect answered by the echo route; whether the credentials survive follows the oracle's origin comparison."""
    url = f"{base}/redir?status=302&to={enc(ref)}"
    final, target = resolved(url, ref)
    host = canonical(host_header(concrete(final)))
    same = origin(concrete(url)) == origin(concrete(final))
    expected = {**KEPT_ALL, "host": [host]} if same else stripped(host)
    send(f"send_request/{ident}", url=url, headers=list(headers) + X_ECHO, tags=tags,
         expect=echo(url=final, target=request_target(concrete(final)), hdr=expected), note=note)


def group_d12():
    rules("D12")
    unusable = "a port that is not a run of digits, or is above 65535, makes the request InvalidRequest without a connection"
    for label, port in {
        "65536": "65536", "65537": "65537", "99999": "99999", "100000": "100000", "leading-zeros-65536": "0065536",
        "many-leading-zeros-65536": "000000000000065536", "2-pow-31-minus-1": "2147483647", "2-pow-31": "2147483648",
        "2-pow-32-minus-1": "4294967295", "2-pow-32": "4294967296", "2-pow-32-plus-1": "4294967297", "2-pow-63-minus-1": "9223372036854775807",
        "2-pow-63": "9223372036854775808", "2-pow-64": "18446744073709551616", "2-pow-64-plus-1": "18446744073709551617", "forty-four-nines": "9" * 44,
    }.items():
        send(f"send_request/port-unusable-above-65535-{label}", url=f"http://127.0.0.1:{port}/x", expect=INVALID, note=unusable)
    for label, port in {
        "letters": "abc", "trailing-letter": "80a", "leading-letter": "a80", "plus-sign": "+80", "minus-sign": "-80", "hex-prefix": "0x50",
        "underscore": "8_0", "decimal-point": "80.0", "exponent": "1e2", "comma": "8,0", "semicolon": "8;0", "apostrophe": "8'0", "bang": "80!",
        "plus-inside": "8+0", "percent-encoded-digits": "%38%30", "tilde": "80~", "dollar": "$80", "equals": "80=",
    }.items():
        send(f"send_request/port-unusable-non-digit-{label}", url=f"http://127.0.0.1:{port}/x", expect=INVALID, note=unusable)
    for ident, url in [("ipv6-non-digit", "http://[::1]:abc/x"), ("ipv6-above-65535", "http://[::1]:65536/x"), ("https-non-digit", "https://127.0.0.1:abc/x"),
                       ("https-above-65535", "https://127.0.0.1:65536/x"), ("userinfo-above-65535", "http://u:p@127.0.0.1:65536/x"),
                       ("no-path-non-digit", "http://127.0.0.1:abc"), ("query-only-above-65535", "http://127.0.0.1:65536?x=1")]:
        send(f"send_request/port-unusable-{ident}", url=url, expect=INVALID, note=unusable)
    for label, port in {"letters": "{N_PORT}abc", "letter": "{N_PORT}x", "decimal-point": "{N_PORT}.0", "underscore": "{N_PORT}_0", "plus-prefix": "+{N_PORT}",
                        "minus-prefix": "-{N_PORT}", "hex-prefix": "0x{N_PORT}", "percent-escape": "{N_PORT}%20", "extra-digits": "{N_PORT}00000"}.items():
        send(f"send_request/port-unusable-live-port-with-junk-{label}", url=f"http://127.0.0.1:{port}/x", expect=INVALID,
             note=unusable + "; the number in front is the never-contact server's port, so a client that reads a numeric prefix connects to it")
    for label, port in {"zero": "0", "two-zeros": "00", "four-zeros": "0000", "twelve-zeros": "0" * 12}.items():
        send(f"send_request/port-zero-{label}-is-attempted", url=f"http://127.0.0.1:{port}/x", expect=NETWORK, note="port 0 is attempted and fails as NetworkFailed")
    send("send_request/port-leading-zeros-of-a-closed-port-is-attempted", url="http://127.0.0.1:0{CLOSED_PORT}/x", expect=NETWORK,
         note="the decimal value is used: the connection to the closed port is attempted and refused")
    note = "the port is a run of digits whose decimal value is used: leading zeros are allowed and never shown in Host; Response.url keeps the URL as given"
    for label, port in {"one-zero": "0{A_PORT}", "two-zeros": "00{A_PORT}", "twenty-eight-zeros": "0" * 28 + "{A_PORT}"}.items():
        direct(f"port-leading-zeros-{label}-decimal-value-used", f"http://127.0.0.1:{port}/echo", note=note)
    direct("port-userinfo-with-colon-and-letters", "http://u:abc@127.0.0.1:{A_PORT}/echo", note="the userinfo ends at the last @: its colon and letters are not the port")
    direct("port-userinfo-password-that-looks-like-a-large-port", "http://u:99999@127.0.0.1:{A_PORT}/echo", note="the userinfo ends at the last @")
    direct("port-userinfo-with-leading-zeros", "http://u:p@127.0.0.1:0{A_PORT}/echo", note=note)
    # Locations
    lead = "the port of a Location is read like the port of a URL: the decimal value counts, so leading zeros change neither the origin nor Host"
    redirect_to("port-location-leading-zeros-same-origin", "{A}", "http://127.0.0.1:0{A_PORT}/echo", note=lead)
    redirect_to("port-location-leading-zeros-from-other-origin", "{B}", "http://127.0.0.1:0{A_PORT}/echo", note=lead)
    redirect_to("port-location-leading-zeros-scheme-relative", "{A}", "//127.0.0.1:00{A_PORT}/echo", note=lead)
    redirect_to("port-location-leading-zeros-relative-path-keeps-them", "http://127.0.0.1:0{A_PORT}", "/echo", note="a relative Location keeps the base authority as written")
    url = "{A}/redir?status=302&to=" + enc("http://127.0.0.1:0/x")
    send("send_request/port-location-zero-is-attempted", url=url, expect=NETWORK, note="a followed redirect to port 0 is attempted and fails as NetworkFailed")
    for label, ref in {
        "non-digit": "http://127.0.0.1:abc/x", "above-65535": "http://127.0.0.1:65536/x", "99999": "http://127.0.0.1:99999/x", "negative": "http://127.0.0.1:-1/x",
        "hex-prefix": "http://127.0.0.1:0x50/x", "live-port-then-letters": "http://127.0.0.1:{A_PORT}abc/echo", "live-port-decimal-point": "http://127.0.0.1:{A_PORT}.0/echo",
        "live-port-underscore": "http://127.0.0.1:{A_PORT}_0/echo", "scheme-relative-above-65535": "//127.0.0.1:65536/x", "ipv6-non-digit": "http://[::1]:abc/x",
        "userinfo-then-above-65535": "http://u:p@127.0.0.1:65536/x", "thirty-nines": "http://127.0.0.1:" + "9" * 30 + "/x",
    }.items():
        url = f"{{A}}/redir?status=302&to={enc(ref)}"
        send(f"send_request/port-location-unusable-{label}-not-followed", url=url, headers=X_ECHO,
             expect={**ok(status=302, url=canonical(url), body="redirecting\n"), "value.headers": std_headers(12, first=[("Location", canonical(ref))])},
             note="a Location whose port has a non-digit or is above 65535 is not followed: the 3xx is returned")
    # the empty port and ":080" need 127.0.0.1:80, the largest port needs 127.0.0.1:65535: see README.md (namespace pass)
    p80 = ["port80"]
    default = "an empty port means the scheme default, and a port equal to the default is never shown in Host"
    for label, port in {"080": "080", "0080": "0080", "00080": "00080", "many-zeros": "0" * 13 + "80"}.items():
        direct(f"port-leading-zeros-default-port-{label}-is-not-shown", f"http://127.0.0.1:{port}/echo", tags=p80, note=default)
    direct("port-empty-means-the-default", "http://127.0.0.1:/echo", tags=p80, note=default)
    direct("port-empty-without-path", "http://127.0.0.1:", tags=p80, note=default)
    direct("port-empty-before-query", "http://127.0.0.1:?x=1", tags=p80, headers=X_ECHO, note=default)
    direct("port-empty-before-fragment", "http://127.0.0.1:#frag", tags=p80, note=default)
    direct("port-empty-uppercase-host", "http://LOCALHOST:/echo", tags=p80, note=default)
    direct("port-leading-zeros-default-port-userinfo-uppercase-host", "http://u:p@LOCALHOST:080/echo", tags=p80, note=default)
    redirect_to("port-location-leading-zeros-default-port-same-origin", "http://127.0.0.1:080", "http://127.0.0.1:0080/echo", tags=p80, note=default)
    redirect_to("port-location-empty-port-same-origin-as-explicit", "http://127.0.0.1:80", "http://127.0.0.1:/echo", tags=p80, note=default)
    redirect_to("port-location-explicit-default-same-origin-as-empty", "http://127.0.0.1:", "http://127.0.0.1:080/echo", tags=p80, note=default)
    redirect_to("port-location-default-port-from-other-origin", "{A}", "http://127.0.0.1:080/echo", tags=p80, note=default)
    redirect_to("port-location-empty-port-from-other-origin", "{A}", "http://127.0.0.1:/echo", tags=p80, note=default)
    top = ["port65535"]
    largest = "65535 is the largest usable port; Host shows it"
    direct("port-65535-is-usable", "http://127.0.0.1:65535/echo", tags=top, note=largest)
    direct("port-65535-with-leading-zero", "http://127.0.0.1:065535/echo", tags=top, note=largest)
    direct("port-65535-with-many-leading-zeros", "http://127.0.0.1:0000000000065535/echo", tags=top, note=largest)
    redirect_to("port-location-65535-from-other-origin", "{A}", "http://127.0.0.1:65535/echo", tags=top, note=largest)
    send("send_request/port-65536-is-unusable-while-65535-exists", url="http://127.0.0.1:65536/echo", tags=top, expect=INVALID, note=unusable)
    url = "{A}/redir?status=302&to=" + enc("http://127.0.0.1:65536/echo")
    send("send_request/port-location-65536-not-followed-while-65535-exists", url=url, headers=X_ECHO, tags=top,
         expect={**ok(status=302, url=canonical(url), body="redirecting\n"), "value.headers": std_headers(12, first=[("Location", "http://127.0.0.1:65536/echo")])},
         note="a Location above 65535 is not followed")
    v6 = ["ipv6"]
    direct("port-ipv6-leading-zeros", "http://[::1]:0{V6_PORT}/echo", tags=v6, note=note)
    redirect_to("port-ipv6-location-leading-zeros-same-origin", "{V6}", "http://[::1]:0{V6_PORT}/echo", tags=v6, note=lead)


# ---- D13 --------------------------------------------------------------------------------------------------------


def group_d13():
    rules("D13")
    note = "a request header value with a character above U+007F is InvalidRequest; no connection is attempted"
    for label, value in {
        "e-acute": "caf\u00e9", "u0080": "\u0080", "u0080-inside": "a\u0080b", "u00ff": "\u00ff", "u0100": "\u0100", "emoji": "\U0001f600", "line-separator": "\u2028",
        "byte-order-mark": "\ufeff", "no-break-space": "\u00a0", "cjk": "\u65e5\u672c", "u0080-at-start": "\u0080x", "u0080-at-end": "x\u0080", "max-code-point": "\U0010ffff",
    }.items():
        send(f"send_request/request-header-value-non-ascii-{label}", url="{N}/text", headers=[("X-Keep", value)], expect=INVALID, note=note)
    send("send_request/request-header-value-non-ascii-in-cookie", url="{N}/text", headers=[("Cookie", "a=\u00e9")], expect=INVALID, note=note)
    send("send_request/request-header-value-non-ascii-in-authorization", url="{N}/text", headers=[("Authorization", "Bearer \u00e9")], expect=INVALID, note=note)
    send("send_request/request-header-value-non-ascii-in-host", url="{N}/text", headers=[("Host", "h\u00e9.example")], expect=INVALID, note=note)
    send("send_request/request-header-value-non-ascii-second-of-two", url="{N}/text", headers=[("X-Ok", "1"), ("X-Keep", "\u00e9")], expect=INVALID, note=note)
    send("send_request/request-header-value-non-ascii-first-of-two", url="{N}/text", headers=[("X-Keep", "\u00e9"), ("X-Ok", "1")], expect=INVALID, note=note)
    send("send_request/request-header-value-non-ascii-with-body", "Post", "{N}/text", headers=[("X-Keep", "\u00e9")], body="b", expect=INVALID, note=note)
    send("send_request/request-header-value-non-ascii-wins-over-connection-failure", url="{CLOSED}/text", headers=[("X-Keep", "\u00e9")], expect=INVALID,
         note=note + "; InvalidRequest wins over the NetworkFailed a connection attempt would give")
    punct = "".join(chr(code) for code in range(0x21, 0x7F))
    send("send_request/request-header-value-printable-ascii-passes", url="{A}/echo", headers=[("X-Keep", punct)], expect=echo(hdr={"x-keep": [punct]}),
         note="every printable ASCII character is allowed in a request header value")
    send("send_request/request-header-value-ascii-with-inner-space-passes", url="{A}/echo", headers=[("X-Keep", "a b  c")], expect=echo(hdr={"x-keep": ["a b  c"]}))


# ---- the decisions through execute --------------------------------------------------------------------------------


# ---- D14 --------------------------------------------------------------------------------------------------------


#: The printable ASCII characters that are neither token characters nor the colon (RFC 9110 delimiters), and the token punctuation.
DELIMITERS = {'"': "double-quote", "(": "left-parenthesis", ")": "right-parenthesis", ",": "comma", "/": "slash", ";": "semicolon", "<": "less-than",
              "=": "equals", ">": "greater-than", "?": "question-mark", "@": "at-sign", "[": "left-bracket", "\\": "backslash", "]": "right-bracket",
              "{": "left-brace", "}": "right-brace"}
PUNCTUATION = {"!": "exclamation-mark", "#": "hash", "$": "dollar", "%": "percent", "&": "ampersand", "'": "apostrophe", "*": "asterisk", "+": "plus",
               "-": "hyphen", ".": "dot", "^": "caret", "_": "underscore", "`": "grave-accent", "|": "vertical-bar", "~": "tilde"}
assert set(PUNCTUATION) == set(TCHAR_PUNCT) and set(DELIMITERS) == {chr(code) for code in range(0x21, 0x7F)} - set(TCHARS) - {":"}


def group_d14():
    rules("D14")
    bad = "a received header line whose name is not one or more HTTP token characters immediately followed by \":\" is NetworkFailed; no partial Response"
    good = "a name of token characters (letters, digits and !#$%&'*+-.^_`|~) followed by \":\" is accepted and kept as received"

    def field(ident, accepted, *lines, around=True, note=None):
        """A 200 whose header block holds these lines (between two valid fields when ``around``); the oracle's verdict on the
        lines must be the one the case intends."""
        assert valid_block(list(lines)) == accepted, (ident, lines)
        raw_block(f"response-header-{ident}", [b"X-Before: 1", *lines, b"X-After: 2"] if around else list(lines), rule="D14", note=note or (good if accepted else bad))

    field("name-space-before-colon", False, b"X-A : v")
    field("name-tab-before-colon", False, b"X-A\t: v")
    field("name-spaces-before-colon", False, b"X-A     : v")
    field("name-space-before-colon-empty-value", False, b"X-A :")
    field("name-space-only-before-colon", False, b" : v")
    field("name-empty", False, b": v")
    field("name-empty-and-value-empty", False, b":")
    field("name-inner-space", False, b"X A: v")
    field("name-inner-tab", False, b"X\tA: v")
    for ident, byte in [("nul", 0x00), ("soh", 0x01), ("vertical-tab", 0x0B), ("form-feed", 0x0C), ("bare-cr", 0x0D), ("bare-lf", 0x0A), ("del", 0x7F)]:
        field(f"name-non-token-char-{ident}", False, b"X" + bytes([byte]) + b"A: v")
    for char, label in DELIMITERS.items():
        field(f"name-non-token-char-{label}", False, f"X{char}A: v".encode())
    field("name-at-sign-first", False, b"@A: v")
    field("name-at-sign-last", False, b"A@: v")
    field("name-only-at-sign", False, b"@: v")
    field("name-non-ascii-utf8", False, b"X-Caf\xc3\xa9: v")
    field("name-non-ascii-latin1", False, b"X-Caf\xe9: v")
    field("name-non-ascii-utf8-with-latin1-value", False, b"X-Caf\xc3\xa9: caf\xe9")
    field("name-non-ascii-latin1-with-utf8-value", False, b"X-Caf\xe9: caf\xc3\xa9")
    field("name-non-ascii-in-every-field", False, b"X-\xc3\xa9: \xc3\xa9", b"X-\xe2\x82\xac: \xe2\x82\xac", around=False)
    field("name-non-ascii-lone-continuation-byte", False, b"X-\x80: v")
    field("name-non-ascii-ff-byte", False, b"X-\xff: v")
    field("name-non-ascii-byte-order-mark-first", False, b"\xef\xbb\xbfX-A: v")
    field("name-non-ascii-no-break-space-utf8", False, b"X-\xc2\xa0A: v")
    field("line-without-colon", False, b"X-NoColon")
    field("line-without-colon-space-and-text", False, b"X-A v")
    field("line-without-colon-single-letter", False, b"X")
    field("line-leading-space-before-name", False, b" X-A: v")
    field("line-leading-tab-before-name", False, b"\tX-A: v")
    fold = "a continuation line (leading whitespace) has no name and no colon: it is not a field line, and nothing is unfolded"
    field("line-obs-fold-continuation", False, b"X-Fold: first", b" second", note=fold)
    field("line-obs-fold-tab-continuation", False, b"X-Fold: first", b"\tsecond", note=fold)
    field("name-not-a-token-first-line", False, b"X@A: v", around=False, note=bad + " (the first line of the block)")
    raw_block("response-header-name-not-a-token-last-line", [], framing=FRAMING + [b"X@A: v"], rule="D14", note=bad + " (the last line, right before the blank line)")
    raw_block("response-header-name-space-before-colon-in-content-length", [], framing=[b"Content-Length : 2", b"Connection: close"], rule="D14",
              note=bad + "; the framing header is a field like any other")
    bad_line = b"X@A: v\r\n"
    final = "/hdr-raw?hex=" + (bad_line + b"Content-Length: 2\r\nConnection: close\r\n").hex()
    send("send_request/response-header-name-not-a-token-in-a-redirect-response", url="{A}/hdr-redirect?to=" + enc("/echo") + "&hex=" + bad_line.hex(), headers=X_ECHO,
         expect=NETWORK, note=bad + "; the redirect (to /echo, valid otherwise) is not followed")
    send("send_request/response-header-name-not-a-token-after-a-followed-redirect", url="{A}/hdr-redirect?to=" + enc(final) + "&hex=" + b"X-Ok: 1\r\n".hex(),
         expect=NETWORK, note=bad + "; here in the final response, after a valid redirect response")
    for codes in ("102", "100", "100,102"):
        send(f"send_request/response-header-name-not-a-token-in-interim-{codes.replace(',', '-and-')}", url=f"{{A}}/interim?codes={codes}&ihex=" + bad_line.hex(),
             expect=NETWORK, note=bad + "; the fields of an interim response are read before the response is discarded")
    send("send_request/response-header-name-not-a-token-in-a-head-response", "Head", "{A}/hdr-raw?hex=" + (bad_line + b"Content-Length: 2\r\nConnection: close\r\n").hex(),
         expect=NETWORK, note=bad)
    field("name-only-tchar-punctuation", True, b"!#$%&'*+-.^_`|~: v")
    field("name-every-token-character", True, TCHARS.encode() + b": v")
    for char, label in PUNCTUATION.items():
        field(f"name-token-char-{label}", True, f"X{char}A: v".encode())
    field("name-digits-only", True, b"123: v")
    field("name-single-letter", True, b"a: v")
    field("name-single-hyphen", True, b"-: v")
    field("name-ends-at-the-first-colon", True, b"X:A: v", note="the name ends at the first colon: the field is X with the value \"A: v\"")
    field("value-with-delimiters", True, b"X-V: \"a\" (b) [c] {d} <e> @ ; , / \\ ? =", note="the name rule does not apply to values")
    field("value-with-colons", True, b"X-Time: 12:30:45", note="only the first colon ends the name")


def group_decisions_through_execute():
    def rendered(status, url, headers, body):
        return "\n".join([f"{status} {canonical(url)}"] + [f"{header['name']}: {header['value']}" for header in headers] + ["", body])

    rules("D7")
    url = "{A}/interim?codes=100,102"
    execute("execute/interim-responses-are-discarded", ["GET", url], expect={"tag": "Ok", "value": rendered(200, url, std_headers(5), "final")})
    rules("D5")
    lines = [b"X-Lead:   lead  ", b"X-Blank:\t"] + FRAMING
    url = "{A}/hdr-raw?hex=" + b"".join(line + b"\r\n" for line in lines).hex()
    execute("execute/header-values-are-trimmed", ["GET", url], expect={"tag": "Ok", "value": rendered(200, url, expected_headers(lines), "ok")})
    rules("D6")
    lines = [b"X-Latin1: caf\xe9", b"X-Utf8: caf\xc3\xa9"] + FRAMING
    url = "{A}/hdr-raw?hex=" + b"".join(line + b"\r\n" for line in lines).hex()
    execute("execute/header-block-decodes-as-latin1", ["GET", url], expect={"tag": "Ok", "value": rendered(200, url, expected_headers(lines), "ok")})
    rules("D12")
    url = "http://127.0.0.1:0{A_PORT}/echo"
    execute("execute/port-with-leading-zeros-is-used-and-shown-as-given", ["GET", url], expect={"tag": "Ok", "value": contains("200 " + canonical(url) + "\n", '"host": ["{A_HOST}"]')})
    execute("execute/port-above-65535", ["GET", "http://127.0.0.1:65536/x"], expect=INVALID)
    execute("execute/port-non-digit", ["GET", "http://127.0.0.1:{N_PORT}abc/x"], expect=INVALID)
    rules("D3")
    execute("execute/dot-segments-in-the-path", ["GET", "{A}/a/./b/../echo"], expect={"tag": "Ok", "value": contains('"target": "/a/echo"', "200 {A}/a/./b/../echo\n")})
    rules("D1")
    url = "{A}/redir?status=302&to=" + enc("/echo") + "&dup=" + enc("/text")
    execute("execute/several-location-fields-return-the-redirect", ["GET", url], expect={"tag": "Ok", "value": contains("302 " + canonical(url) + "\nLocation: /echo\nLocation: /text\n", "\n\nredirecting\n")})
    rules("D14")
    url = "{A}/hdr-raw?hex=" + b"".join(line + b"\r\n" for line in [b"X@A: v"] + FRAMING).hex()
    execute("execute/response-header-name-not-a-token", ["GET", url], expect=NETWORK)


GROUPS = [
    group_d1, group_d2, group_d3, group_d4, group_d5, group_d6, group_d7, group_d8, group_d9, group_d10, group_d11, group_d12, group_d13, group_d14,
    group_decisions_through_execute,
]
