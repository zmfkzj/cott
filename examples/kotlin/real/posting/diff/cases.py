#!/usr/bin/env python3
"""The differential case table: the contract rules R1-R7 and the general behavior (this file) and the decisions D1-D14
(decisions.py), built with the helpers of casekit.py.

Every expected value is derived from the contract text (client.cott, send_request) or computed by the independent
oracles in oracle.py (RFC 3986 resolution, Unicode Table 3-7/3-8 decoding, URL-character validity, request target, Host
and port derivation, header-block decoding).  None is copied from an implementation's output.  Every case carries an
``expect`` that BOTH implementations must meet.

    python3 cases.py             per-group counts
    python3 cases.py --write F   dump the case list as JSON
    python3 cases.py --list      case ids and tags
"""

from __future__ import annotations

import hashlib
import json
import string
import sys
from collections import Counter

import casekit
from casekit import (
    ABSENT,
    CREDS,
    CREDS_NO_HOST,
    INVALID,
    INVALID_ARGS,
    KEPT_ALL,
    LIMIT,
    NETWORK,
    OK,
    STANDARD,
    TCHAR_PUNCT,
    TCHARS,
    VIOLATION,
    add,
    alternating,
    concrete,
    contains,
    cp,
    custom,
    echo,
    execute,
    followed_echo,
    mirror,
    ok,
    place,
    redir,
    render,
    resolved,
    rules,
    send,
    stripped,
)
from decisions import GROUPS as DECISION_GROUPS
from oracle import (
    INVALID_PRINTABLE,
    RFC_ABNORMAL,
    RFC_BASE,
    RFC_NORMAL,
    TABLE_3_8_BYTES,
    VALID_PRINTABLE,
    decode_utf8,
    expected_headers,
    followable,
    host_header,
    origin,
    request_target,
    url_characters_valid,
)


# ---- parse_method ---------------------------------------------------------------------------------------------


def group_parse_method():
    rules("methods")
    for method in STANDARD:
        forms = {
            "upper": method, "lower": method.lower(), "title": method.capitalize(),
            "alt-lower-first": alternating(method, False), "alt-upper-first": alternating(method, True),
        }
        for form, source in forms.items():
            add(f"parse_method/standard-{method.lower()}-{form}", "parse_method", source=source,
                expect={"tag": "Ok", "value.variant": method.capitalize()})
    customs = {
        "purge-lower": "purge", "purge-upper": "PURGE", "purge-title": "Purge", "m-search": "M-SEARCH",
        "propfind": "PROPFIND", "trace": "TRACE", "connect": "CONNECT", "link": "LINK", "unlink": "UNLINK",
        "copy": "COPY", "move": "MOVE", "lock": "LOCK", "mkcol": "MKCOL", "x-lower": "x", "x-upper": "X",
        "a1": "a1", "digit-0": "0", "digit-9": "9", "gets": "GETS", "ge": "GE", "pos": "POS", "heads": "HEADS",
        "optionss": "OPTIONSS", "get-dash": "GET-", "dash-get": "-GET", "patch1": "PATCH1", "delet": "DELET",
        "deleted": "deleted", "options-underscore": "Options_", "get-dot": "get.", "get-tilde": "get~",
        "get-bang": "Get!", "long-256": "a" * 256, "long-mixed-case": "Ab" * 64,
    }
    for name, source in customs.items():
        add(f"parse_method/custom-{name}", "parse_method", source=source,
            expect={"tag": "Ok", "value.variant": "Custom", "value.name": source})
    for name, source in {
        "all-punctuation": TCHAR_PUNCT, "lowercase-alphabet": string.ascii_lowercase,
        "uppercase-alphabet": string.ascii_uppercase, "digits": string.digits, "every-tchar": TCHARS,
    }.items():
        add(f"parse_method/tchars-{name}", "parse_method", source=source,
            expect={"tag": "Ok", "value.variant": "Custom", "value.name": source})
    for code in range(128):  # every ASCII character alone and after GET
        ch = chr(code)
        alone = {"tag": "Ok", "value.variant": "Custom", "value.name": ch} if ch in TCHARS else INVALID
        after = {"tag": "Ok", "value.variant": "Custom", "value.name": "GET" + ch} if ch in TCHARS else INVALID
        add(f"parse_method/ascii-{cp(ch)}-alone", "parse_method", source=ch, expect=alone)
        add(f"parse_method/ascii-get-then-{cp(ch)}", "parse_method", source="GET" + ch, expect=after)
    for ch in ' "(),/:;<=>?@[\\]{}':
        add(f"parse_method/non-token-{cp(ch)}-inside-get", "parse_method", source="GE" + ch + "T", expect=INVALID)
    for code in [0x80, 0x9F, 0xA0, 0xAD, 0xB5, 0xC0, 0xDF, 0xE9, 0xFF, 0x130, 0x131, 0x17F, 0x394, 0x2028, 0x2029,
                 0x200B, 0x2160, 0x212A, 0xFEFF, 0xFF21, 0x10000, 0x1F600, 0x10FFFF]:
        add(f"parse_method/non-ascii-{cp(chr(code))}-alone", "parse_method", source=chr(code), expect=INVALID)
        add(f"parse_method/non-ascii-get-then-{cp(chr(code))}", "parse_method", source="GET" + chr(code), expect=INVALID)
    invalid = {
        "empty": "", "spaces-3": "   ", "tab": "\t", "lf": "\n", "cr": "\r", "crlf": "\r\n", "nul": "\u0000",
        "get-space-x": "GET X", "leading-space": " GET", "trailing-space": "GET ", "trailing-tab": "GET\t",
        "trailing-lf": "GET\n", "trailing-cr": "GET\r", "embedded-nul": "G\u0000ET", "del": "\u007f",
        "c0-0x01": "\u0001", "c0-0x1f": "\u001f", "custom-with-space": "PUR GE", "colon": "A:B",
        "http-version": "GET/1.1", "e-acute": "\u00e9", "get-with-accent": "G\u00c9T", "cjk": "\u65e5\u672c\u8a9e",
        "emoji": "\U0001f600", "nbsp": "\u00a0", "fullwidth-get": "\uff27\uff25\uff34", "long-s-post": "Po\u017fT",
        "dotless-i-options": "OPT\u0131ONS", "dotted-i-options": "OPT\u0130ONS", "kelvin-sign": "\u212a",
        "zero-width-space-suffix": "GET\u200b", "bom-prefix": "\ufeffGET", "combining-accent": "GE\u0301T",
        "get-newline-x": "GET\nX",
    }
    for name, source in invalid.items():
        add(f"parse_method/invalid-{name}", "parse_method", source=source, expect=INVALID)


# ---- parse_arguments ------------------------------------------------------------------------------------------


def group_parse_arguments():
    rules("arguments")
    url = "http://example.test/items"
    ok_request = {"tag": "Ok", "value.headers.#": 0, "value.timeout_ms": 30000}
    add("parse_arguments/zero-arguments", "parse_arguments", arguments=[], expect=INVALID_ARGS)
    add("parse_arguments/one-argument", "parse_arguments", arguments=["GET"], expect=INVALID_ARGS)
    add("parse_arguments/one-argument-invalid-method", "parse_arguments", arguments=["GET X"], expect=INVALID_ARGS,
        note="the argument-count error precedes the method error")
    add("parse_arguments/four-arguments", "parse_arguments", arguments=["GET", url, "body", "extra"], expect=INVALID_ARGS)
    add("parse_arguments/four-arguments-invalid-method", "parse_arguments", arguments=["GET X", url, "b", "c"],
        expect=INVALID_ARGS, note="the argument-count error precedes the method error")
    add("parse_arguments/five-arguments", "parse_arguments", arguments=["GET", url, "b", "c", "d"], expect=INVALID_ARGS)
    add("parse_arguments/two-get-lower", "parse_arguments", arguments=["get", url],
        expect={**ok_request, "value.method.variant": "Get", "value.url": url, "value.body": ""})
    for method in STANDARD:
        add(f"parse_arguments/two-{method.lower()}-mixed-case", "parse_arguments", arguments=[alternating(method, True), url],
            expect={**ok_request, "value.method.variant": method.capitalize(), "value.body": ""})
    add("parse_arguments/two-custom-purge", "parse_arguments", arguments=["purge", url],
        expect={**ok_request, "value.method.variant": "Custom", "value.method.name": "purge"})
    add("parse_arguments/three-post-json", "parse_arguments", arguments=["post", "https://api.example/items", '{"id":1}'],
        expect={**ok_request, "value.method.variant": "Post", "value.body": '{"id":1}'})
    add("parse_arguments/three-empty-body", "parse_arguments", arguments=["POST", url, ""], expect={**ok_request, "value.body": ""})
    body = "h\u00e9llo\nw\u00f6rld \U0001f600"
    add("parse_arguments/three-unicode-body", "parse_arguments", arguments=["PUT", url, body], expect={**ok_request, "value.body": body})
    add("parse_arguments/three-whitespace-body", "parse_arguments", arguments=["PATCH", url, "  x\r\n y \t"],
        expect={**ok_request, "value.body": "  x\r\n y \t"}, note="URL and BODY are copied verbatim")
    for name, value in {"garbage": "not a url", "empty": "", "ftp": "ftp://example.test/x", "space-and-unicode": "http://h\u00e9.test/\u65e5\u672c?q=\U0001f600 x"}.items():
        add(f"parse_arguments/url-not-validated-{name}", "parse_arguments", arguments=["GET", value],
            expect={**ok_request, "value.url": value}, note="the URL is not validated here")
    add("parse_arguments/two-invalid-method", "parse_arguments", arguments=["GET X", url], expect=INVALID)
    add("parse_arguments/two-empty-method", "parse_arguments", arguments=["", url], expect=INVALID)
    add("parse_arguments/three-invalid-method", "parse_arguments", arguments=["G\u00c9T", url, "b"], expect=INVALID)
    add("parse_arguments/two-long-s-post-method", "parse_arguments", arguments=["Po\u017fT", url], expect=INVALID)
    add("parse_arguments/two-custom-tchars-method", "parse_arguments", arguments=[TCHAR_PUNCT, url],
        expect={**ok_request, "value.method.variant": "Custom", "value.method.name": TCHAR_PUNCT})


# ---- render_response ------------------------------------------------------------------------------------------


def group_render_response():
    rules("render")
    def rendered(status, url, headers, body):
        lines = [f"{status} {url}"] + [f"{name}: {value}" for name, value in headers] + ["", body]
        return {"tag": "Str", "value": "\n".join(lines)}

    def case(ident, status=200, url="http://api.example/", headers=(), body="", **kw):
        render(ident, status, url, headers, body, expect=rendered(status, url, headers, body), **kw)

    case("render_response/contract-example", 404, "http://api.example/items/9", [("Content-Type", "text/plain"), ("X-Trace", "a1")], "missing\nitem")
    case("render_response/no-headers-empty-body", 204, "http://api.example/", (), "")
    case("render_response/no-headers-with-body", 200, "http://api.example/", (), "hello")
    case("render_response/one-header-empty-body", 200, "http://api.example/", [("A", "b")], "")
    case("render_response/duplicate-headers-kept-in-order", 200, "http://api.example/", [("Set-Cookie", "a=1"), ("X", "1"), ("Set-Cookie", "b=2")], "ok")
    case("render_response/empty-header-value", 200, "http://api.example/", [("X-Empty", "")], "b")
    case("render_response/header-value-with-colon-space", 200, "http://api.example/", [("Location", "http://x/a: b")], "")
    case("render_response/header-name-not-validated", 200, "http://api.example/", [(" X ", " y ")], "")
    case("render_response/body-blank-lines-and-trailing-lf", 200, "http://api.example/", [], "a\n\nb\n")
    case("render_response/body-crlf", 200, "http://api.example/", [("A", "b")], "l1\r\nl2\r\n")
    case("render_response/body-only-lf", 200, "http://api.example/", [], "\n")
    case("render_response/body-leading-lf", 200, "http://api.example/", [], "\nbody")
    case("render_response/body-tab-and-nul", 200, "http://api.example/", [], "a\tb\u0000c")
    case("render_response/unicode-everywhere", 200, "http://h\u00e9.example/\u65e5\u672c", [("X-\u00dcn\u00ef", "c\u00f6d\u00e9 \U0001f600")], "h\u00e9llo \U0001f600 \u65e5\u672c\u8a9e")
    case("render_response/empty-url", 200, "", [], "b")
    case("render_response/url-with-lf", 200, "http://x/\nfoo", [], "b")
    case("render_response/header-value-with-lf", 200, "http://api.example/", [("X", "a\nb")], "b")
    for status in (0, 1, 99, 100, 199, 200, 301, 599, 600, 999, 1000, 65535):
        case(f"render_response/status-{status}", status, "http://api.example/", [], "b")
    case("render_response/many-headers", 200, "http://api.example/", [(f"X-{i}", f"v{i}") for i in range(50)], "b")
    case("render_response/long-body-70k", 200, "http://api.example/", [("A", "b")], "x" * 70000)


# ---- boundary violations: a Str with a lone surrogate -------------------------------------------------------------


def group_violations():
    rules("boundary")
    note = "a Str holding a lone UTF-16 surrogate is a boundary contract violation in both runtimes, before any implementation code runs"
    for name, source in {"high": "\ud800", "low": "\udc00", "reversed-pair": "\udc00\ud800", "after-token": "GET\ud800",
                         "inside-custom-token": "PUR\udbffGE"}.items():
        add(f"parse_method/violation-lone-surrogate-{name}", "parse_method", source=source, expect=VIOLATION, note=note)
    add("parse_arguments/violation-lone-surrogate-in-method", "parse_arguments", arguments=["\ud800", "http://h/"], expect=VIOLATION, note=note)
    add("parse_arguments/violation-lone-surrogate-in-url", "parse_arguments", arguments=["GET", "http://h/\udc00"], expect=VIOLATION, note=note)
    add("parse_arguments/violation-lone-surrogate-in-body", "parse_arguments", arguments=["POST", "http://h/", "a\ud83db"], expect=VIOLATION, note=note)
    render("render_response/violation-lone-surrogate-in-body", body="a\udfffb", expect=VIOLATION, note=note)
    render("render_response/violation-lone-surrogate-in-url", url="http://x/\ud800", expect=VIOLATION, note=note)
    render("render_response/violation-lone-surrogate-in-header-name", headers=[("X\ud800", "v")], expect=VIOLATION, note=note)
    render("render_response/violation-lone-surrogate-in-header-value", headers=[("X", "v\udc00")], expect=VIOLATION, note=note)
    send("send_request/violation-lone-surrogate-in-url", url="{N}/a\ud800", expect=VIOLATION, note=note)
    send("send_request/violation-lone-surrogate-in-body", "Post", "{N}/text", body="a\udfffb", expect=VIOLATION, note=note)
    send("send_request/violation-lone-surrogate-in-header-value", url="{N}/text", headers=[("X-Keep", "v\ud800")], expect=VIOLATION, note=note)
    send("send_request/violation-lone-surrogate-in-header-name", url="{N}/text", headers=[("X\udc00", "v")], expect=VIOLATION, note=note)
    send("send_request/violation-lone-surrogate-in-custom-method", custom("PU\ud800RGE"), "{N}/text", expect=VIOLATION, note=note)
    execute("execute/violation-lone-surrogate-in-url-argument", ["GET", "{N}/a\ud800"], expect=VIOLATION, note=note)
    execute("execute/violation-lone-surrogate-in-method-argument", ["\ud800", "{N}/text"], expect=VIOLATION, note=note)
    execute("execute/violation-lone-surrogate-in-body-argument", ["POST", "{N}/text", "x\udfff"], expect=VIOLATION, note=note)


# ---- send_request: InvalidRequest, decided from the request alone ------------------------------------------------


def group_invalid_request():
    rules("invalid-request")
    n = "{N}/text"
    send("send_request/invalid-timeout-zero", url=n, timeout=0, expect=INVALID)
    send("send_request/invalid-timeout-zero-post-body", "Post", n, body="x", timeout=0, expect=INVALID)
    send("send_request/invalid-timeout-zero-unreachable-host", url="{CLOSED}/text", timeout=0, expect=INVALID,
         note="InvalidRequest wins over the NetworkFailed a connection attempt would give")
    urls = {
        "ftp": "ftp://{N_HOST}/x", "file": "file:///etc/passwd", "javascript": "javascript:alert(1)",
        "uppercase-scheme": "HTTP://{N_HOST}/text", "mixed-case-scheme": "Http://{N_HOST}/text",
        "https-uppercase-scheme": "HTTPS://{N_HOST}/text", "no-scheme": "{N_HOST}/text", "scheme-relative": "//{N_HOST}/text",
        "leading-space": " {N}/text", "empty": "", "path-only": "/text", "http-colon-only": "http:", "https-colon-only": "https:",
        "http-single-slash": "http:/{N_HOST}/text", "httpx": "httpx://{N_HOST}/text", "ws-scheme": "ws://{N_HOST}/text",
    }
    for name, url in urls.items():
        send(f"send_request/invalid-url-{name}", url=url, expect=INVALID)
    no_host = {
        "http-empty-authority": "http://", "https-empty-authority": "https://", "http-empty-authority-path": "http:///text",
        "http-port-only": "http://:8080/text", "http-userinfo-only": "http://user@/text", "http-userinfo-port-only": "http://user@:8080/x",
        "http-query-only": "http://?q=1", "http-fragment-only": "http://#frag", "https-port-only": "https://:8443/",
    }
    for name, url in no_host.items():
        send(f"send_request/invalid-no-host-{name}", url=url, expect=INVALID)
    send("send_request/invalid-url-unreachable-host-ftp", url="ftp://127.0.0.1:1/x", expect=INVALID)
    names = {
        "empty": "", "space": " ", "tab": "\t", "nbsp": "\u00a0", "spaces-3": "   ", "with-space": "Bad Name", "colon": "X:Y",
        "crlf": "X\r\nY", "lf": "X\nY", "unicode": "X-\u00e9", "slash": "X/Y", "parens": "X(Y)", "trailing-space": "X-Keep ",
        "leading-tab": "\tX-Keep", "at-sign": "X@Y", "quote": 'X"Y', "nul": "X\u0000Y", "emoji": "\U0001f600",
    }
    for name, header in names.items():
        send(f"send_request/invalid-header-name-{name}", "Post", n, [(header, "v")], body="b", expect=INVALID)
    send("send_request/invalid-header-name-second-of-two", url=n, headers=[("X-Ok", "1"), ("", "x")], expect=INVALID)
    send("send_request/invalid-header-name-unreachable-host", url="{CLOSED}/text", headers=[(" ", "x")], expect=INVALID,
         note="InvalidRequest wins over the NetworkFailed a connection attempt would give")
    values = {
        "cr": "a\rb", "lf": "a\nb", "crlf-injection": "a\r\nInjected: 1", "leading-cr": "\rb", "trailing-lf": "a\n",
        "only-lf": "\n", "only-crlf": "\r\n", "lf-space-fold": "a\n b",
    }
    for name, value in values.items():
        send(f"send_request/invalid-header-value-{name}", url=n, headers=[("X-Test", value)], expect=INVALID)
    send("send_request/invalid-header-value-second-of-two", url=n, headers=[("X-Ok", "1"), ("X-Bad", "a\nb")], expect=INVALID)
    send("send_request/invalid-header-value-unreachable-host", url="{CLOSED}/text", headers=[("X", "a\nb")], expect=INVALID)
    methods = {
        "space": "GET X", "empty": "", "e-acute": "\u00e9", "crlf": "A\r\nB", "colon": "A:B", "inner-space": "A B", "tab": "\t",
        "nul": "GE\u0000T", "slash": "GET/1.1", "trailing-space": "PURGE ", "emoji": "\U0001f600", "long-s-post": "Po\u017fT",
        "at-sign": "A@B",
    }
    for name, method in methods.items():
        send(f"send_request/invalid-custom-method-{name}", custom(method), n, expect=INVALID)
    send("send_request/invalid-custom-method-unreachable-host", custom("GET X"), "{CLOSED}/text", expect=INVALID)


def group_url_characters():
    """Rule 1: every character outside the URL set, and every malformed %HH, is InvalidRequest; the whole set is not."""
    rules("R1")
    bad_percent = {
        "lone": "%", "one-digit": "%4", "non-hex-pair": "%zz", "hex-then-non-hex": "%4g", "non-hex-then-hex": "%g4",
        "double": "%%41", "arabic-indic-digits": "%\u0664\u0664", "fullwidth-digits": "%\uff14\uff11", "sign": "%+1",
    }
    invalid: dict[str, str] = {}
    for ch in INVALID_PRINTABLE:
        invalid[f"printable-{cp(ch)}"] = ch
    invalid["space"] = " "
    for code in list(range(0x20)) + [0x7F]:
        invalid[f"control-{cp(chr(code))}"] = chr(code)
    for code in [0x80, 0x9F, 0xA0, 0xAD, 0xFF, 0x100, 0x2028, 0xFEFF, 0xFF0F, 0x1F600, 0x10FFFF]:
        invalid[f"non-ascii-{cp(chr(code))}"] = chr(code)
    for name, text in bad_percent.items():
        invalid[f"percent-{name}"] = text
    # "z" follows the inserted text: it is not a hexadecimal digit, so "%4" + "z" stays malformed.
    for name, text in invalid.items():
        assert not url_characters_valid("a" + text + "z"), name
        send(f"send_request/url-invalid-{name}-in-path", url="{N}/a" + text + "z", expect=INVALID)
        send(f"send_request/url-invalid-{name}-in-fragment", url="{N}/a#x" + text + "z", expect=INVALID,
             note="the fragment is never sent, but it is part of the URL")
    representative = {
        "space": " ", "dquote": '"', "lt": "<", "lbrace": "{", "pipe": "|", "backslash": "\\", "caret": "^", "grave": "`",
        "tab": "\t", "nul": "\u0000", "del": "\u007f", "c1-U+0080": "\u0080", "e-acute": "\u00e9", "emoji": "\U0001f600",
        "percent-lone": "%", "percent-one-digit": "%4", "percent-non-hex": "%zz",
    }
    for label, text in representative.items():
        assert not url_characters_valid("a" + text + "z"), label
        send(f"send_request/url-invalid-{label}-in-query", url="{N}/a?x" + text + "z", expect=INVALID)
        send(f"send_request/url-invalid-{label}-in-userinfo", url="http://u" + text + "z@{N_HOST}/a", expect=INVALID)
        send(f"send_request/url-invalid-{label}-in-host", url="http://h" + text + "z.{N_HOST}/a", expect=INVALID)
    for name, url in {"percent-at-end-of-path": "{N}/a%", "one-digit-at-end-of-path": "{N}/a%4", "percent-at-end-of-query": "{N}/a?%",
                      "one-digit-at-end-of-fragment": "{N}/a#%4", "percent-at-end-of-url": "{N}/a%4%"}.items():
        assert not url_characters_valid(url), url
        send(f"send_request/url-invalid-{name}", url=url, expect=INVALID)
    # Valid: each URL character verbatim in the request target (a strict URI parser would reject several of them).
    for ch in VALID_PRINTABLE:
        if ch not in "?#":
            url = "{A}/p" + ch + "q/echo"
            send(f"send_request/url-valid-{cp(ch)}-in-path", url=url, expect=echo(target="/p" + ch + "q/echo", url=url))
        if ch != "#":
            url = "{A}/echo?x" + ch + "y"
            send(f"send_request/url-valid-{cp(ch)}-in-query", url=url, expect=echo(target="/echo?x" + ch + "y", url=url))
    every = "".join(VALID_PRINTABLE)
    send("send_request/url-valid-every-character-in-fragment", url="{A}/echo#" + every, expect=echo(target="/echo", url="{A}/echo#" + every),
         note="the fragment is not sent but stays in Response.url")
    send("send_request/url-valid-every-character-in-query", url="{A}/echo?" + every.replace("#", ""),
         expect=echo(target="/echo?" + every.replace("#", ""), url="{A}/echo?" + every.replace("#", "")))
    userinfo = "us%3Aer:p!$&'()*+,;=~-._"
    send("send_request/url-valid-userinfo-with-sub-delims", url=f"http://{userinfo}@{{A_HOST}}/echo",
         expect=echo(target="/echo", host="{A_HOST}", hdr={"authorization": ABSENT}, url=f"http://{userinfo}@{{A_HOST}}/echo"))
    # Percent-encoded octets are sent exactly as written.
    for name, path in {
        "path-mixed": "/a%2Fb/%7e%7E/%41/%00/%ff/%25/echo", "path-hex-case": "/%aB%Ab%AB%ab/echo",
        "path-encoded-slash-and-dot": "/a%2F..%2Fb/%2e%2e/echo", "path-encoded-space-and-utf8": "/a%20b/%C3%A9/echo",
    }.items():
        send(f"send_request/url-percent-verbatim-{name}", url="{A}" + path, expect=echo(target=path, url="{A}" + path))
    query = "/echo?a=%7e&b=%7E&c=%41&d=%2f&e=%25&f=%00&g=%FF&h=%c3%a9&i=100%25"
    send("send_request/url-percent-verbatim-query", url="{A}" + query, expect=echo(target=query, url="{A}" + query))


# ---- send_request: request line, Host, userinfo -----------------------------------------------------------------


def group_target_and_host():
    rules("R2")
    for ident, url, target in [
        ("path-root", "{A}/", "/"), ("path-empty", "{A}", "/"), ("path-empty-with-query", "{A}?x=1", "/?x=1"),
        ("path-empty-with-empty-query", "{A}?", "/?"), ("path-empty-with-fragment", "{A}#frag", "/"),
        ("path-empty-with-query-and-fragment", "{A}?x#frag", "/?x"), ("empty-query", "{A}/echo?", "/echo?"),
        ("empty-query-with-fragment", "{A}/echo?#frag", "/echo?"), ("question-mark-inside-fragment", "{A}/echo#frag?x=1", "/echo"),
        ("fragment-only", "{A}/echo#frag", "/echo"), ("empty-fragment", "{A}/echo#", "/echo"), ("query-and-fragment", "{A}/echo?a=1&b=2#f", "/echo?a=1&b=2"),
        ("double-slash-path", "{A}//echo", "//echo"), ("triple-slash-path", "{A}///echo", "///echo"),
        ("trailing-slash-path", "{A}/echo/", "/echo/"), ("root-with-empty-query", "{A}/?", "/?"),
    ]:
        send(f"send_request/target-{ident}", url=url, headers=[("X-Echo", "1")], expect=echo(target=target, url=url))
        assert request_target(concrete(url)) == target, (url, request_target(concrete(url)), target)
    send("send_request/target-http-version", url="{A}/echo", expect=echo(version="HTTP/1.1", method="GET", target="/echo"),
         note="Send one HTTP/1.1 request")
    send("send_request/target-query-value-with-hash-escape", url="{A}/echo?a=%23b#c", expect=echo(target="/echo?a=%23b"))
    rules("R3")
    for ident, url in [
        ("default", "{A}/echo"), ("uppercase-host", "http://LOCALHOST:{A_PORT}/echo"), ("mixed-case-host", "http://LocalHost:{A_PORT}/echo"),
        ("userinfo", "http://user:pw@{A_HOST}/echo"), ("userinfo-empty", "http://:@{A_HOST}/echo"),
        ("userinfo-percent-encoded", "http://us%40er:p%3Aw@{A_HOST}/echo"), ("userinfo-user-only", "http://user@{A_HOST}/echo"),
        ("userinfo-and-uppercase-host", "http://user:pw@LOCALHOST:{A_PORT}/echo"),
    ]:
        expected_host = place(host_header(concrete(url)))
        send(f"send_request/host-{ident}", url=url,
             expect=echo(host=expected_host, target="/echo", hdr={"authorization": ABSENT, "cookie": ABSENT}, url=url),
             note="Host is the URL host as written (case kept, no userinfo) plus :port for a non-default port; userinfo is neither sent nor used; Response.url keeps the URL as given")
    send("send_request/host-caller-header-replaces-default", url="{A}/echo", headers=[("Host", "custom.example")],
         expect=echo(host="custom.example", target="/echo"))
    send("send_request/host-caller-header-any-case", url="{A}/echo", headers=[("hOsT", "custom.example")],
         expect=echo(host="custom.example", target="/echo"))
    send("send_request/host-caller-header-keeps-its-position", url="{A}/echo",
         headers=[("X-First", "f"), ("Host", "custom.example"), ("X-Second", "s")],
         expect=echo(hdr={"host": ["custom.example"]}, order=["x-first", "host", "x-second"]),
         note="request.headers are sent in order, a caller-supplied Host included")
    send("send_request/host-caller-header-with-userinfo-url", url="http://user:pw@{A_HOST}/echo", headers=[("Host", "custom.example")],
         expect=echo(host="custom.example", hdr={"authorization": ABSENT}))
    send("send_request/host-ipv6-literal-brackets-accepted", url="http://[::1]:1/x", expect=NETWORK,
         note="an IPv6 literal is a valid host (brackets are URL characters); nothing listens on [::1]:1, so the failure is a connection failure")


# ---- send_request: exchanges ------------------------------------------------------------------------------------


def group_exchanges():
    rules("exchange")
    send("send_request/get-text", expect={**ok(status=200, url="{A}/text", body="hello world"), "value.headers.#": 3,
                                          "value.headers.0.name": "Content-Type", "value.headers.0.value": "text/plain; charset=utf-8"})
    send("send_request/get-unicode-body", url="{A}/unicode", expect=ok(status=200, body="h\u00e9llo w\u00f6rld \u2014 \u65e5\u672c\u8a9e \U0001f600\n"))
    send("send_request/get-empty-body", url="{A}/empty", expect=ok(status=200, body=""))
    send("send_request/get-no-path-url", url="{A}", expect=ok(status=200, url="{A}", body="index"),
         note="a URL without a path is valid; Response.url is the URL as given")
    send("send_request/get-root-path-url", url="{A}/", expect=ok(url="{A}/", body="index"))
    for code in (201, 202, 400, 404, 418, 500, 503):
        send(f"send_request/get-status-{code}", url=f"{{A}}/status?code={code}", expect=ok(status=code, body=f"status {code}\n"))
    send("send_request/get-status-204-no-body", url="{A}/status?code=204", expect=ok(status=204, body=""))
    send("send_request/get-status-304-no-body", url="{A}/status?code=304", expect=ok(status=304, body=""))
    for code in ("600", "999", "099"):
        send(f"send_request/get-status-outside-100-599-{code}", url=f"{{A}}/status?code={code}", expect=NETWORK)
    send("send_request/get-response-headers-order-duplicates-case", url="{A}/headers",
         expect={**ok(status=200, body="ok"), "value.headers.#": 11, "value.headers.0.name": "X-Zeta", "value.headers.3.value": "first",
                 "value.headers.5.name": "x-dup", "value.headers.5.value": "second", "value.headers.6.value": ""},
         note="received order, duplicates and the received name case are kept")
    send("send_request/get-chunked-response", url="{A}/chunked", expect=ok(status=200, body="chunk-1;chunk-2;chunk-3"))
    send("send_request/get-close-delimited-response", url="{A}/close-delimited", expect=ok(status=200, body="read until close"),
         note="neither Content-Length nor chunked: the body extends to the connection close")
    send("send_request/head-text", "Head", "{A}/text", expect={**ok(status=200, body=""), "value.headers.1.value": "11"},
         note="HEAD: Content-Length is announced but no body follows")
    send("send_request/head-chunked", "Head", "{A}/chunked", expect=ok(status=200, body=""))
    send("send_request/head-status-404", "Head", "{A}/status?code=404", expect=ok(status=404, body=""))
    send("send_request/head-close-delimited", "Head", "{A}/close-delimited", expect=ok(status=200, body=""))
    send("send_request/head-with-body", "Head", "{A}/text", body="hello", expect=ok(status=200, body=""))
    for name, ms in {"u32-max": 4294967295, "2-pow-31": 2147483648, "2-pow-31-minus-1": 2147483647}.items():
        send(f"send_request/get-timeout-{name}", timeout=ms, expect=ok(status=200, body="hello world"),
             note="timeout_ms is a U32: it must not overflow into a negative or zero timeout")
    send("send_request/get-slow-within-timeout", url="{A}/slow?ms=200", expect=ok(status=200, body="slow done"))
    send("send_request/get-charset-header-ignored-iso-8859-1", url="{A}/charset?cs=iso-8859-1", expect=ok(body="h\u00e9llo \u00fcber"),
         note="a Content-Type charset is ignored: the body is always UTF-8")
    send("send_request/get-charset-header-ignored-utf-16", url="{A}/charset?cs=utf-16", expect=ok(body="h\u00e9llo \u00fcber"))
    send("send_request/get-charset-header-ignored-shift_jis", url="{A}/charset?cs=shift_jis", expect=ok(body="h\u00e9llo \u00fcber"))
    # request line, headers and body as received
    json_type = [("Content-Type", "application/json")]
    send("send_request/options-echo", "Options", "{A}/echo", expect=echo(method="OPTIONS", body="", body_bytes=0))
    send("send_request/post-json-body", "Post", "{A}/echo", json_type, '{"id":1}',
         expect=echo(method="POST", body='{"id":1}', body_bytes=8, hdr={"content-type": ["application/json"]}))
    send("send_request/post-body-no-headers", "Post", "{A}/echo", (), "hello", expect=echo(method="POST", body="hello", body_bytes=5, hdr={"authorization": ABSENT, "cookie": ABSENT}),
         note="no invented Authorization or Cookie")
    send("send_request/post-empty-body", "Post", "{A}/echo", expect=echo(method="POST", body="", body_bytes=0), note="an empty body sends no payload")
    send("send_request/put-body", "Put", "{A}/echo", json_type, '{"a":[1,2]}', expect=echo(method="PUT", body='{"a":[1,2]}', body_bytes=11))
    send("send_request/patch-body", "Patch", "{A}/echo", (), "patch me", expect=echo(method="PATCH", body="patch me", body_bytes=8))
    send("send_request/delete-no-body", "Delete", "{A}/echo", expect=echo(method="DELETE", body="", body_bytes=0))
    send("send_request/delete-with-body", "Delete", "{A}/echo", (), "why", expect=echo(method="DELETE", body="why", body_bytes=3))
    send("send_request/get-with-body", "Get", "{A}/echo", (), "hello", expect=echo(method="GET", body="hello", body_bytes=5),
         note="a non-empty body is sent whatever the method")
    send("send_request/post-unicode-body", "Post", "{A}/echo", (), "h\u00e9llo \U0001f600", expect=echo(method="POST", body="h\u00e9llo \U0001f600", body_bytes=11),
         note="the body is sent as UTF-8 bytes")
    send("send_request/post-body-crlf-and-nul", "Post", "{A}/echo", (), "a\r\nb\u0000c", expect=echo(method="POST", body="a\r\nb\u0000c", body_bytes=6))
    send("send_request/post-large-body-200k", "Post", "{A}/echo", (), "y" * 200000, expect=echo(method="POST", body_bytes=200000))
    send("send_request/custom-purge", custom("PURGE"), "{A}/echo", expect=echo(method="PURGE", body="", body_bytes=0))
    send("send_request/custom-lowercase-get-unchanged", custom("get"), "{A}/echo", expect=echo(method="get"),
         note="a Custom name is sent unchanged, even when it spells a standard method")
    send("send_request/custom-lowercase-purge-unchanged", custom("purge"), "{A}/echo", expect=echo(method="purge"))
    send("send_request/custom-tchar-method", custom(TCHAR_PUNCT), "{A}/echo", expect=echo(method=TCHAR_PUNCT))
    send("send_request/custom-method-with-body", custom("M-SEARCH"), "{A}/echo", (), "h\u00e9llo \U0001f600",
         expect=echo(method="M-SEARCH", body="h\u00e9llo \U0001f600", body_bytes=11))
    send("send_request/headers-order-and-duplicates", "Get", "{A}/echo",
         [("X-Multi", "1"), ("X-First", "f"), ("X-Multi", "2"), ("X-Second", "s"), ("X-Multi", "3")],
         expect=echo(hdr={"x-multi": ["1", "2", "3"], "x-first": ["f"], "x-second": ["s"]},
                     order_no_host=["x-multi", "x-first", "x-multi", "x-second", "x-multi"]),
         note="request.headers are sent in order, duplicates included")
    send("send_request/header-name-case-preserved-insensitive", "Get", "{A}/echo", [("x-KEEP", "1"), ("AUTHORIZATION", "t")],
         expect=echo(hdr={"x-keep": ["1"], "authorization": ["t"]}))
    send("send_request/header-value-empty", "Get", "{A}/echo", [("X-Keep", "")], expect=echo(hdr={"x-keep": [""]}))
    send("send_request/header-value-with-tab", "Get", "{A}/echo", [("X-Keep", "a\tb")], expect=echo(hdr={"x-keep": ["a\tb"]}))
    send("send_request/header-value-with-colon-and-equals", "Get", "{A}/echo", [("Cookie", "a=b; c=d:e")], expect=echo(hdr={"cookie": ["a=b; c=d:e"]}))
    send("send_request/header-token-chars-name", "Get", "{A}/echo", [(TCHAR_PUNCT, "1")], expect=echo(status=200))
    send("send_request/long-header-value-8000", "Get", "{A}/echo", [("X-Keep", "v" * 8000)], expect=echo(hdr={"x-keep": ["v" * 8000]}))
    send("send_request/many-request-headers-100", "Get", "{A}/echo", [("X-Multi", f"m{i}") for i in range(100)],
         expect=echo(hdr={"x-multi": [f"m{i}" for i in range(100)]}))
    send("send_request/long-url-query-8000", "Get", "{A}/echo?q=" + "q" * 8000, expect=echo(target="/echo?q=" + "q" * 8000, url="{A}/echo?q=" + "q" * 8000))
    send("send_request/credentials-sent-without-redirect", "Get", "{A}/echo",
         [("Authorization", "Bearer s3cret"), ("Cookie", "sid=1"), ("Proxy-Authorization", "Basic eHl6"), ("X-Keep", "yes")],
         expect=echo(hdr={"authorization": ["Bearer s3cret"], "cookie": ["sid=1"], "proxy-authorization": ["Basic eHl6"], "x-keep": ["yes"]}))


# ---- redirects --------------------------------------------------------------------------------------------------


def group_redirects():
    rules("redirects")
    followed = ok(status=200, url="{A}/text", body="hello world")
    for code in (301, 302, 303, 307, 308):
        send(f"send_request/redirect-{code}-get-followed", url=f"{{A}}/redir?status={code}&to=/text", expect=followed)
        send(f"send_request/redirect-{code}-head-followed", "Head", f"{{A}}/redir?status={code}&to=/text", expect=ok(status=200, url="{A}/text", body=""),
             note="HttpMethod.Head follows too; the final response has no body")
    send("send_request/redirect-absolute-location-same-origin", url="{A}/redir?status=302&to={A}/text", expect=followed)
    for ident, path, ref in [
        ("relative-sibling", "/dir/redir", "echo"), ("relative-dot-slash", "/dir/redir", "./echo"),
        ("relative-parent", "/dir/sub/redir", "../echo"), ("relative-absolute-path", "/dir/sub/redir", "/echo"),
        ("relative-query-and-path", "/dir/redir", "echo?a=1&b=2"), ("relative-query-only", "/dir/redir", "?q=1"),
        ("relative-double-parent", "/a/b/redir", "../../echo"), ("relative-dot-segments-inside", "/a/redir", "b/../c/./echo"),
        ("relative-empty-segment-kept", "/a/redir", "b//echo"), ("relative-beyond-root", "/redir", "../../echo"),
        ("relative-beyond-root-deep", "/a/redir", "../../../../../echo"), ("relative-doc-example-empty-segment", "/a/b/redir", "..//echo"),
        ("relative-fragment-kept", "/dir/redir", "echo#frag"), ("relative-encoded-dots-are-literal", "/dir/sub/redir", "%2e%2e/echo"),
        ("relative-percent-verbatim", "/dir/redir", "a%20b/%C3%A9/echo"), ("relative-encoded-slash-is-literal", "/dir/redir", "a%2f..%2fecho"),
        ("relative-dot-only-segment-name", "/dir/redir", "..;x/echo"), ("relative-trailing-empty-query", "/dir/redir", "echo?"),
        ("relative-trailing-empty-fragment", "/dir/redir", "echo#"), ("relative-slash-only", "/dir/redir", "/"),
    ]:
        followed_echo(f"send_request/redirect-{ident}", redir(path, ref), ref)
    followed_echo("send_request/redirect-scheme-relative-same-origin", redir("/redir", "//{A_HOST}/echo"), "//{A_HOST}/echo")
    followed_echo("send_request/redirect-absolute-with-dot-segments", redir("/redir", "http://{A_HOST}/x/./y/../echo"), "http://{A_HOST}/x/./y/../echo")
    send("send_request/redirect-doc-example-query-only", url="{A}/dir/redir?status=302&to=%3Fq%3D1", headers=[("X-Echo", "1")],
         expect=echo(target="/dir/redir?q=1", url="{A}/dir/redir?q=1"),
         note="contract example: base http://h/dir/redir with Location ?q=1 resolves to http://h/dir/redir?q=1")
    send("send_request/redirect-doc-example-beyond-root", url="{A}/redir?status=302&to=../../echo",
         expect=echo(target="/echo", url="{A}/echo"), note="contract example: base http://h/redir with ../../echo resolves to http://h/echo")
    send("send_request/redirect-doc-example-empty-segment", url="{A}/a/b/c", headers=mirror("send_request/redirect-doc-example-empty-segment", "..//g", at="/a/b/c"),
         expect=echo(target="/a//g", url="{A}/a//g"), note="contract example: base http://h/a/b/c with ..//g resolves to http://h/a//g")
    send("send_request/redirect-same-origin-keeps-every-header", url="{A}/redir?status=302&to=/echo", headers=CREDS,
         expect=echo(hdr={**KEPT_ALL, "host": ["custom.example"]}), note="a redirect within the same origin keeps every header, Host included")
    send("send_request/redirect-same-origin-host-header-position", url="{A}/redir?status=302&to=/echo", headers=[("X-First", "f"), ("Host", "custom.example"), ("X-Second", "s")],
         expect=echo(order=["x-first", "host", "x-second"]))
    # chains and the redirect limit
    send("send_request/redirect-chain-9-followed", url="{A}/chain?n=9", expect=ok(status=200, url="{A}/chain?n=0", body="end"))
    send("send_request/redirect-chain-10-followed", url="{A}/chain?n=10", expect=ok(status=200, url="{A}/chain?n=0", body="end"), note="exactly 10 redirects are followed")
    send("send_request/redirect-chain-11-last-3xx-returned", url="{A}/chain?n=11",
         expect={**ok(status=302, url="{A}/chain?n=1", body="redirecting\n"), "value.headers.0.value": "/chain?n=0"},
         note="a further redirect response is returned as received")
    send("send_request/redirect-chain-12-head", "Head", "{A}/chain?n=12", expect=ok(status=302, url="{A}/chain?n=2", body=""))
    send("send_request/redirect-chain-10-head-followed", "Head", "{A}/chain?n=10", expect=ok(status=200, url="{A}/chain?n=0", body=""))
    send("send_request/redirect-self-loop-stops-at-10", url="{A}/loop", expect=ok(status=302, url="{A}/loop"))
    # methods that never follow
    for code in (301, 302, 303, 307, 308):
        send(f"send_request/redirect-{code}-post-not-followed", "Post", f"{{A}}/redir?status={code}&to=/text", (), "x",
             expect={**ok(status=code, url=f"{{A}}/redir?status={code}&to=/text", body="redirecting\n"), "value.headers.0.name": "Location", "value.headers.0.value": "/text"})
    for name, method, code in (("put-307", "Put", 307), ("patch-308", "Patch", 308), ("delete-302", "Delete", 302), ("options-302", "Options", 302),
                               ("custom-purge-301", custom("PURGE"), 301), ("custom-uppercase-get-302", custom("GET"), 302),
                               ("custom-lowercase-get-303", custom("get"), 303)):
        send(f"send_request/redirect-{name}-not-followed", method, f"{{A}}/redir?status={code}&to=/text",
             expect=ok(status=code, url=f"{{A}}/redir?status={code}&to=/text"),
             note="only HttpMethod.Get and HttpMethod.Head follow redirects; a Custom name that spells GET does not")
    send("send_request/redirect-post-cross-origin-not-followed", "Post", "{A}/x-out", CREDS, "x", expect=ok(status=302, url="{A}/x-out"))
    for code in (300, 304, 305):
        send(f"send_request/redirect-{code}-not-a-followed-status", url=f"{{A}}/redir?status={code}&to=/text", expect=ok(status=code, url=f"{{A}}/redir?status={code}&to=/text"))
    send("send_request/redirect-302-without-location-returned", url="{A}/redir?status=302&nolocation=1&to=/text", expect={**ok(status=302, body="redirecting\n"), "value.headers.#": 3})
    send("send_request/redirect-301-without-location-returned", url="{A}/redir?status=301&nolocation=1&to=/text", expect=ok(status=301))
    send("send_request/redirect-http-to-https-is-followed", url="{A}/redir?status=302&to=https://{A_HOST}/text", expect=NETWORK,
         note="http -> https is not a downgrade: the hop is followed and the TLS handshake against a plain listener fails")


def group_origins():
    """Rule 5 and the credential rule."""
    rules("R5")
    send("send_request/redirect-cross-origin-port-strips-credentials", url="{A}/x-out", headers=CREDS,
         expect=echo(url="{B}/echo", target="/echo", hdr=stripped("{B_HOST}")),
         note="Authorization, Cookie, Proxy-Authorization and Host are not sent to the new origin; Host is replaced by the URL's own host; X-Keep is kept")
    send("send_request/redirect-cross-origin-strips-mixed-case-names", url="{A}/x-out",
         headers=[("aUtHoRiZaTiOn", "t"), ("COOKIE", "c"), ("proxy-AUTHORIZATION", "p"), ("hOsT", "custom.example"), ("x-keep", "yes")],
         expect=echo(url="{B}/echo", hdr=stripped("{B_HOST}")))
    for name, status in (("307", 307), ("301", 301), ("303", 303), ("308", 308)):
        send(f"send_request/redirect-cross-origin-absolute-location-{name}", url=f"{{A}}/redir?status={status}&to={{B}}/echo", headers=CREDS,
             expect=echo(url="{B}/echo", hdr=stripped("{B_HOST}")))
    send("send_request/redirect-cross-origin-scheme-relative", url="{A}/redir?status=302&to=//{B_HOST}/echo", headers=CREDS, expect=echo(url="{B}/echo", hdr=stripped("{B_HOST}")))
    send("send_request/redirect-same-origin-hop-then-cross-origin", url="{A}/redir?status=302&to=/x-out", headers=CREDS, expect=echo(url="{B}/echo", hdr=stripped("{B_HOST}")))
    send("send_request/redirect-cross-origin-round-trip-stays-stripped", url="{A}/x-bounce", headers=CREDS,
         expect=echo(url="{A}/echo", hdr=stripped("{A_HOST}")), note="A -> B -> A: nothing is re-added when returning to A, and Host is A's own")
    send("send_request/redirect-cross-origin-without-caller-credentials", url="{A}/x-out", headers=[("X-Keep", "yes")],
         expect=echo(url="{B}/echo", hdr=stripped("{B_HOST}")))
    send("send_request/redirect-cross-origin-host-name-differs-same-port", url="{A}/redir?status=302&to=http://localhost:{A_PORT}/echo", headers=CREDS_NO_HOST,
         expect=echo(url="http://localhost:{A_PORT}/echo", hdr=stripped("localhost:{A_PORT}")),
         note="127.0.0.1 -> localhost on the same port: the host of the origin differs")
    send("send_request/redirect-cross-origin-host-case-kept-in-host-header", url="{A}/redir?status=302&to=http://LOCALHOST:{A_PORT}/echo", headers=CREDS_NO_HOST,
         expect=echo(url="http://LOCALHOST:{A_PORT}/echo", hdr=stripped("LOCALHOST:{A_PORT}")))
    send("send_request/redirect-same-origin-host-case-insensitive", url="http://localhost:{A_PORT}/redir?status=302&to=http://LOCALHOST:{A_PORT}/echo", headers=CREDS_NO_HOST,
         expect=echo(url="http://LOCALHOST:{A_PORT}/echo", hdr={**KEPT_ALL, "host": ["LOCALHOST:{A_PORT}"]}),
         note="origins compare hosts ASCII case-insensitively, so every header is kept; Host follows the new URL as written")
    send("send_request/redirect-same-origin-userinfo-ignored", url="{A}/redir?status=302&to=http://user:pw@{A_HOST}/echo", headers=CREDS_NO_HOST,
         expect=echo(url="http://user:pw@{A_HOST}/echo", target="/echo", hdr={**KEPT_ALL, "host": ["{A_HOST}"]}),
         note="userinfo is not part of the origin, is never sent and never replaces the caller's Authorization; Response.url keeps it")
    send("send_request/redirect-same-origin-explicit-port-in-location", url="{A}/redir?status=302&to=http://{A_HOST}/echo", headers=CREDS_NO_HOST,
         expect=echo(url="{A}/echo", hdr={**KEPT_ALL, "host": ["{A_HOST}"]}))
    # An https:// hop cannot be served here (no trusted TLS listener); both http->https cases are NetworkFailed above.
    # Location resolution against an https base is therefore not covered.


# ---- RFC 3986 reference resolution through Location -------------------------------------------------------------


def group_resolution():
    rules("R4")
    base = "{A}/b/c/d;p?q"

    def mirrored(ident, base_url, ref, at=None, more=(), **kw):
        final, target = resolved(base_url, ref)
        headers = mirror(ident, ref, at=at, more=more)
        if followable(target):
            wire = request_target(concrete(final))
            send(ident, url=base_url, headers=headers, expect=echo(target=wire, url=final, method="GET"), **kw)
        else:
            send(ident, url=base_url, headers=headers,
                 expect={**ok(status=302, url=base_url, body="redirecting\n"), "value.headers.0.name": "Location", "value.headers.0.value": ref}, **kw)
        return followable(target)

    # RFC 3986 section 5.4, the examples that stay on the base's server (base http://a/b/c/d;p?q mirrored on {A})
    for section, table in (("5.4.1", RFC_NORMAL), ("5.4.2", RFC_ABNORMAL)):
        for number, (reference, want) in enumerate(table, 1):
            if reference == "//g":
                continue  # resolves to http://g, another host: not reachable from the fixtures
            ident = f"send_request/rfc3986-{section}-{number:02d}"
            follows = mirrored(ident, base, reference, note=f"RFC 3986 {section}: {reference!r} = {want!r} against the base {RFC_BASE}")
            if follows:
                assert place(want.replace("http://a", "{A}", 1)) == resolved(base, reference)[0], (reference, want)
            else:
                assert want in ("g:h", "http:g"), want
    extra = [
        "../../../../../g", "/./../g", "/a/../../g", "g/../../h", "g/./../../h", "./g/./h/../i", "..;x/g", ".;x", "%2e/g", "%2e%2e/g",
        ".%2e/g", "g%2f../h", "g//h", "g//", "/g//h", "//{A_HOST}/g//h", "/", "?", "#", "?#", "g?", "g#", "g?#", "g?y?z", "g#s#t",
        "?y/../x", ";", "g;x;y", "d;p?q", "./d;p?q", "../c/d;p?q", "d;p", "d;p?q#f", "g/.", "g/..", "g/../", "./.", "././g", ".././g",
        "../../../", "//{A_HOST}", "//{A_HOST}?y", "//{A_HOST}#z", "//{A_HOST}/", "//{A_HOST}/g?y#s", "//{A_HOST}/../g", "//{A_HOST}/g/./h",
        "//u@{A_HOST}/g", "//u:p@{A_HOST}/g", "http://{A_HOST}/g", "http://{A_HOST}/./g/../h", "http://{A_HOST}", "http://{A_HOST}?y",
        "http://{A_HOST}#z", "http://{A_HOST}/g?y#s", "http://{A_HOST}/../g", "http://{A_HOST}/g%2f..%2fh", "http://u@{A_HOST}/g",
        "g?y=a/./b", "g#a/../b", "g;x=1?y=2#z",
    ]
    for number, reference in enumerate(extra, 1):
        mirrored(f"send_request/resolve-{number:02d}", base, reference, note=f"reference {reference!r} resolved by RFC 3986 5.2 (oracle.resolve)")
    # references that do not resolve to a followable URL: the 3xx response is returned
    for number, reference in enumerate([
        "g:h", "http:g", "//", "///g", "mailto:x@y", "urn:x:y", "data:text/plain,hi", "tel:+1234", "file:///etc/passwd", "ftp://{A_HOST}/g",
        "ws://{A_HOST}/g", "http:", "https:", "http://", "https://", "http://:80/g", "http://u@/g", "http:///g", "https:g", "javascript:alert(1)",
        "http://:", "//:80", "//u@/g", "x-y.z+w:abc",
    ], 1):
        assert not mirrored(f"send_request/not-followed-{number:02d}", base, reference,
                            note=f"{reference!r} resolves to something that is not http(s) or has no host: the 3xx is returned"), reference
    # base variants: the base fragment is not inherited, an empty base path merges to "/", the base authority is kept
    for number, reference in enumerate(["g", "?y", "", "#s", "g#s", ".", "../g", "/g", "g?"], 1):
        mirrored(f"send_request/resolve-base-fragment-{number:02d}", "{A}/b/c/d;p?q#basefrag", reference,
                 note="the fragment of the base is not inherited; Response.url keeps a URL as given only when nothing was followed")
    for number, reference in enumerate(["g", "?y", "#s", "", "./g", "../g", "g/h", "/g", "//{A_HOST}/g", "g?y#s"], 1):
        mirrored(f"send_request/resolve-empty-base-path-{number:02d}", "{A}", reference, at="/", more=[("X-Echo", "1")],
                 note="RFC 3986 5.2.3: with an empty base path the merge yields \"/\" + the reference path")
    for number, reference in enumerate(["g", "?y", "", "/g", "//{A_HOST}/g"], 1):
        mirrored(f"send_request/resolve-empty-base-path-with-query-{number:02d}", "{A}?x", reference, at="/", more=[("X-Echo", "1")])
    for number, reference in enumerate(["g", "/g", "?y", "", "//{A_HOST}/g", "../g"], 1):
        mirrored(f"send_request/resolve-base-userinfo-{number:02d}", "http://u:p@{A_HOST}/b/c/d;p?q", reference,
                 note="a relative reference keeps the base authority, userinfo included; userinfo is still never sent")
    for number, reference in enumerate(["g", "/g", "?y", "#s"], 1):
        mirrored(f"send_request/resolve-base-uppercase-host-{number:02d}", "http://LOCALHOST:{A_PORT}/b/c/d;p?q", reference,
                 note="the base authority is kept exactly as written")
    send("send_request/resolve-empty-location-is-the-base", url=base, headers=mirror("send_request/resolve-empty-location-is-the-base", ""),
         expect=echo(target="/b/c/d;p?q", url=base, method="GET"),
         note="an empty Location is a Location header whose reference is empty: it resolves to the base URL (RFC 3986 5.4.1)")
    # https and other origins from a Location
    send("send_request/resolve-https-location-is-followed", url=base, headers=mirror("send_request/resolve-https-location-is-followed", "https://{A_HOST}/g"),
         expect=NETWORK, note="http -> https is followed; the TLS handshake against a plain listener fails")


def group_invalid_locations():
    """A Location with a character outside the URL set (or a malformed %HH) is not followed: the 3xx is returned."""
    rules("R4")

    def add_location(ident, raw: bytes, **kw):
        url = "{A}/redir?status=302&to_hex=" + raw.hex()
        lines = [b"Location: " + raw, b"Content-Type: text/plain; charset=utf-8", b"Content-Length: 12", b"Connection: close"]
        send(ident, url=url, headers=[("X-Echo", "1")],
             expect={**ok(status=302, url=url, body="redirecting\n"), "value.headers": expected_headers(lines)}, **kw)

    for ch in INVALID_PRINTABLE + " ":
        text = "/ec" + ch + "ho"
        assert not url_characters_valid(text)
        add_location(f"send_request/location-invalid-{cp(ch)}", text.encode("ascii"))
    add_location("send_request/location-invalid-U+0009-tab", b"/ec\tho")
    for label, raw in {"latin1-e9": b"/ec\xe9ho", "utf8-c3a9": b"/ec\xc3\xa9ho", "utf8-emoji": b"/ec\xf0\x9f\x98\x80ho", "utf8-fullwidth-solidus": b"/ec\xef\xbc\x8fho"}.items():
        add_location(f"send_request/location-invalid-non-ascii-{label}", raw, rule="D6",
                     note="the Location bytes are not URL characters, so the 3xx is returned; the values of its header block are decoded as a whole (ASCII, else valid UTF-8, else ISO-8859-1)")
    for label, text in {"lone": "/ec%ho", "one-digit": "/ec%4ho", "non-hex-pair": "/ec%zzho", "double": "/ec%%41ho", "at-end": "/echo%",
                        "one-digit-at-end": "/echo%4", "absolute-with-bad-percent": "http://{A_HOST}/echo%zz"}.items():
        add_location(f"send_request/location-invalid-percent-{label}", text.encode("ascii"))
    send("send_request/location-valid-percent-followed-verbatim", url="{A}/redir?status=302&to=/ec%2568o", headers=[("X-Echo", "1")],
         expect=echo(target="/ec%68o", url="{A}/ec%68o"), note="a well-formed %68 stays as written")


# ---- decoding ---------------------------------------------------------------------------------------------------


def group_decoding():
    rules("R6")
    def body(ident, raw: bytes, **kw):
        text = decode_utf8(raw)
        send(ident, url="{A}/binary?hex=" + raw.hex(), expect=ok(status=200, body=text), **kw)

    body("send_request/decode-contract-example-eda080", bytes.fromhex("eda080"), note="the bytes ED A0 80 become three U+FFFD")
    body("send_request/decode-table-3-8", TABLE_3_8_BYTES,
         note="Unicode Table 3-8: 61 F1 80 80 E1 80 C2 62 80 63 80 BF 64 -> a FFFD FFFD FFFD b FFFD c FFFD FFFD d")
    body("send_request/decode-bom-kept", bytes.fromhex("efbbbf78"), note="a leading byte order mark is kept as U+FEFF")
    body("send_request/decode-bom-in-the-middle", bytes.fromhex("61efbbbf62"))
    body("send_request/decode-nul-kept", bytes.fromhex("610062"))
    body("send_request/decode-6361ff", bytes.fromhex("6361ff"))
    for label, hex_bytes in {
        "ascii": "48656c6c6f", "two-byte-min-c280": "c280", "two-byte-max-dfbf": "dfbf", "three-byte-min-e0a080": "e0a080",
        "three-byte-before-surrogates-ed9fbf": "ed9fbf", "three-byte-after-surrogates-ee8080": "ee8080", "three-byte-max-efbfbf": "efbfbf",
        "four-byte-min-f0908080": "f0908080", "four-byte-max-f48fbfbf": "f48fbfbf", "noncharacter-fffe-efbfbe": "efbfbe",
        "euro-e282ac": "e282ac", "emoji-f09f9880": "f09f9880", "mixed-valid": "61c3a9e282acf09f988062",
    }.items():
        body(f"send_request/decode-valid-{label}", bytes.fromhex(hex_bytes))
    for lead in range(0x80, 0x100):
        raw = bytes([0x61, lead, 0x62])
        body(f"send_request/decode-single-byte-{lead:02x}-between-ascii", raw)
    # boundaries of Table 3-7 for every multi-byte lead: valid extremes, second byte just outside, truncations
    table = {0xC2: (0x80, 0xBF, 1), 0xDF: (0x80, 0xBF, 1), 0xE0: (0xA0, 0xBF, 2), 0xE1: (0x80, 0xBF, 2), 0xEC: (0x80, 0xBF, 2),
             0xED: (0x80, 0x9F, 2), 0xEE: (0x80, 0xBF, 2), 0xEF: (0x80, 0xBF, 2), 0xF0: (0x90, 0xBF, 3), 0xF1: (0x80, 0xBF, 3),
             0xF3: (0x80, 0xBF, 3), 0xF4: (0x80, 0x8F, 3)}
    for lead, (low, high, follow) in table.items():
        tail = [0x80] * (follow - 1)
        for label, second in (("low-1", low - 1), ("low", low), ("high", high), ("high+1", high + 1)):
            if 0 <= second <= 0xFF:
                body(f"send_request/decode-lead-{lead:02x}-second-{label}", bytes([0x61, lead, second, *tail, 0x62]))
        for cut in range(1, follow + 1):
            valid = bytes([lead, low, *([0x80] * (follow - 1))])[:cut]
            body(f"send_request/decode-lead-{lead:02x}-truncated-to-{cut}-then-ascii", bytes([0x61, *valid, 0x62]))
            body(f"send_request/decode-lead-{lead:02x}-truncated-to-{cut}-at-end", bytes([0x61, *valid]))
    for label, hex_bytes in {
        "overlong-c0af": "c0af", "overlong-e080af": "e080af", "overlong-f08080af": "f08080af", "above-max-f4908080": "f4908080",
        "f5-lead": "f5808080", "surrogate-edbfbf": "edbfbf", "lone-continuation-run": "808080", "ff-fe-run": "fffe",
        "four-invalid-leads": "c0c1f5ff", "lead-followed-by-lead": "e2e282ac", "three-byte-cut-by-ascii": "e28241",
        "four-byte-cut-by-lead": "f09f98e282ac",
    }.items():
        body(f"send_request/decode-ill-formed-{label}", bytes.fromhex(hex_bytes))
    # multi-byte characters must survive whatever read-buffer size the client uses (streams stay well-formed)
    def stream(prefix: bytes, unit: bytes, size: int) -> bytes:
        return (prefix + unit * ((size - len(prefix)) // len(unit) + 1))[:size]

    for label, prefix, unit, size in [
        ("euro-3-byte-unit", b"", bytes.fromhex("e282ac"), 300000), ("euro-3-byte-unit-shifted-1", b"a", bytes.fromhex("e282ac"), 300001),
        ("euro-3-byte-unit-shifted-2", b"aa", bytes.fromhex("e282ac"), 300002), ("e-acute-2-byte-unit-shifted-1", b"a", bytes.fromhex("c3a9"), 200001),
        ("emoji-4-byte-unit-shifted-1", b"a", bytes.fromhex("f09f9880"), 400001), ("emoji-4-byte-unit-shifted-2", b"aa", bytes.fromhex("f09f9880"), 400002),
        ("emoji-4-byte-unit-shifted-3", b"aaa", bytes.fromhex("f09f9880"), 400003),
    ]:
        raw = stream(prefix, unit, size)
        assert decode_utf8(raw).encode("utf-8") == raw
        query = f"n={size}&unit_hex={unit.hex()}" + (f"&prefix_hex={prefix.hex()}" if prefix else "")
        send(f"send_request/decode-across-read-chunks-{label}", url="{A}/big?" + query, digest=True,
             expect=ok(status=200, **{"body_digest.utf8_len": size, "body_digest.sha256": hashlib.sha256(raw).hexdigest()}),
             note="a decoder that works per read chunk corrupts characters at chunk boundaries")
        send(f"send_request/decode-across-chunked-pieces-{label}", url="{A}/big?" + query + "&chunked=1", digest=True,
             expect=ok(status=200, **{"body_digest.utf8_len": size, "body_digest.sha256": hashlib.sha256(raw).hexdigest()}))
    invalid_run = bytes([0xFF]) * 100001
    send("send_request/decode-long-run-of-invalid-bytes", url="{A}/big?n=100001&unit_hex=ff", digest=True,
         expect=ok(status=200, **{"body_digest.utf8_len": 3 * 100001, "body_digest.sha256": hashlib.sha256(decode_utf8(invalid_run).encode("utf-8")).hexdigest()}),
         note="100001 invalid bytes become 100001 U+FFFD")
    ill = bytes.fromhex("f09f98") * 60001  # every truncated emoji is one maximal subpart, then the next lead starts afresh
    send("send_request/decode-long-run-of-truncated-sequences", url="{A}/big?n=180003&unit_hex=f09f98", digest=True,
         expect=ok(status=200, **{"body_digest.utf8_len": 3 * 60001, "body_digest.sha256": hashlib.sha256(decode_utf8(ill).encode("utf-8")).hexdigest()}))


# ---- transport failures and the body limit ----------------------------------------------------------------------


def group_failures():
    rules("R7")
    note7 = "a connection closed before the empty line that ends the header block, before all Content-Length bytes, or before the terminating chunk is NetworkFailed; no partial Response"
    send("send_request/fail-connection-dropped", url="{A}/drop", expect=NETWORK)
    send("send_request/fail-connection-dropped-head", "Head", "{A}/drop", expect=NETWORK)
    send("send_request/fail-connection-dropped-post", "Post", "{A}/drop", (), "body", expect=NETWORK)
    send("send_request/fail-dropped-after-status-line", url="{A}/drop-after-status", expect=NETWORK, note=note7)
    send("send_request/fail-dropped-mid-headers", url="{A}/drop-mid-headers", expect=NETWORK, note=note7)
    send("send_request/fail-dropped-before-body", url="{A}/drop-before-body", expect=NETWORK, note=note7)
    send("send_request/fail-dropped-mid-body", url="{A}/drop-mid-body", expect=NETWORK, note=note7)
    send("send_request/fail-dropped-mid-chunked-body", url="{A}/drop-mid-chunk", expect=NETWORK, note=note7)
    send("send_request/fail-dropped-inside-chunk", url="{A}/drop-inside-chunk", expect=NETWORK, note=note7)
    send("send_request/fail-garbage-response", url="{A}/garbage", expect=NETWORK, note="a response that does not start with an HTTP/1.x status line is NetworkFailed")
    for label, line in {"icy": "ICY 200 OK", "http-2": "HTTP/2 200 OK", "non-numeric-status": "HTTP/1.1 abc OK", "two-digit-status": "HTTP/1.1 99 X",
                        "four-digit-status": "HTTP/1.1 1000 X", "status-line-with-leading-garbage": "x HTTP/1.1 200 OK"}.items():
        send(f"send_request/fail-status-line-{label}", url="{A}/status-line?hex=" + line.encode().hex(), expect=NETWORK,
             note="not an HTTP/1.x status line, or a final status outside 100-599")
    send("send_request/status-line-http-1-0-is-accepted", url="{A}/status-line?hex=" + b"HTTP/1.0 200 OK".hex(), expect=ok(status=200, body="ok"),
         note="HTTP/1.0 is an HTTP/1.x status line")
    send("send_request/fail-header-line-without-colon", url="{A}/bad-header-line", expect=NETWORK, note="a header line without a colon is NetworkFailed")
    send("send_request/fail-connection-refused", url="{CLOSED}/text", expect=NETWORK)
    send("send_request/fail-name-resolution", url="http://nonexistent.invalid/", expect=NETWORK, deadline=120)
    send("send_request/fail-name-resolution-sub-delims-host", url="http://exa!mple.invalid/", expect=NETWORK, deadline=120,
         note="! is a URL character, so this is not an InvalidRequest; the name does not resolve")
    send("send_request/fail-https-to-plain-http-port", url="https://{A_HOST}/text", expect=NETWORK, note="a failed TLS handshake is a connection failure")
    send("send_request/fail-read-timeout", url="{A}/slow?ms=2000", timeout=300, expect=NETWORK)
    send("send_request/fail-read-timeout-post", "Post", "{A}/slow?ms=2000", (), "x", timeout=300, expect=NETWORK)
    send("send_request/fail-redirect-target-dropped", url="{A}/redir?status=302&to=/drop", expect=NETWORK)
    send("send_request/fail-redirect-target-status-600", url="{A}/redir?status=302&to=/status%3Fcode%3D600", expect=NETWORK)
    send("send_request/fail-redirect-target-refused", url="{A}/redir?status=302&to={CLOSED}/text", expect=NETWORK)
    send("send_request/fail-redirect-target-truncated-body", url="{A}/redir?status=302&to=/drop-mid-body", expect=NETWORK)
    send("send_request/get-drip-within-read-timeout", url="{A}/drip?chunks=5&gap_ms=500", timeout=1500, tags=["slow"],
         expect=ok(status=200, body="00000000001111111111222222222233333333334444444444"),
         note="timeout_ms bounds each blocking read, not the whole exchange: 2 s of dripping under a 1.5 s timeout succeeds")
    exact = {"body_digest.utf8_len": LIMIT, "body_digest.sha256": hashlib.sha256(b"a" * LIMIT).hexdigest()}
    send("send_request/limit-exact-content-length-ok", url=f"{{A}}/big?n={LIMIT}", digest=True, tags=["slow"], deadline=600, timeout=60000,
         expect=ok(status=200, **exact), note="exactly MAX_RESPONSE_BODY_BYTES is accepted")
    send("send_request/limit-exact-chunked-ok", url=f"{{A}}/big?n={LIMIT}&chunked=1", digest=True, tags=["slow"], deadline=600, timeout=60000, expect=ok(status=200, **exact))
    send("send_request/limit-plus-one-content-length", url=f"{{A}}/big?n={LIMIT + 1}", timeout=60000, expect=NETWORK)
    send("send_request/limit-plus-one-chunked", url=f"{{A}}/big?n={LIMIT + 1}&chunked=1", timeout=60000, expect=NETWORK)
    send("send_request/limit-plus-one-multibyte-counted-before-decoding", url=f"{{A}}/big?n={LIMIT + 1}&unit_hex=e282ac", timeout=60000, expect=NETWORK,
         note="67108865 bytes of 3-byte characters decode to fewer than 67108864 characters but are over the limit")
    send("send_request/limit-plus-one-head-has-no-body", "Head", f"{{A}}/big?n={LIMIT + 1}", expect=ok(status=200, body=""),
         note="HEAD announces a huge Content-Length but carries no body")


# ---- execute ----------------------------------------------------------------------------------------------------


def group_execute():
    rules("execute")
    text = "200 {A}/text\nContent-Type: text/plain; charset=utf-8\nContent-Length: 11\nConnection: close\n\nhello world"
    execute("execute/get-text", ["get", "{A}/text"], expect={**OK, "value": text})
    execute("execute/get-upper", ["GET", "{A}/text"], expect={**OK, "value": text})
    execute("execute/head-text", ["HEAD", "{A}/text"], expect={**OK, "value": "200 {A}/text\nContent-Type: text/plain; charset=utf-8\nContent-Length: 11\nConnection: close\n\n"})
    execute("execute/status-404", ["GET", "{A}/status?code=404"], expect={**OK, "value": "404 {A}/status?code=404\nContent-Type: text/plain; charset=utf-8\nContent-Length: 11\nConnection: close\n\nstatus 404\n"})
    execute("execute/status-204", ["GET", "{A}/status?code=204"], expect={**OK, "value": "204 {A}/status?code=204\nConnection: close\n\n"})
    unicode_text = "h\u00e9llo w\u00f6rld \u2014 \u65e5\u672c\u8a9e \U0001f600\n"
    execute("execute/unicode-response", ["GET", "{A}/unicode"], expect={**OK, "value": "200 {A}/unicode\nContent-Type: text/plain; charset=utf-8\nContent-Length: " + str(len(unicode_text.encode())) + "\nConnection: close\n\n" + unicode_text})
    echo_head = "200 {A}/echo\nContent-Type: application/json\nContent-Length: "
    execute("execute/post-json-body", ["post", "{A}/echo", '{"id":1}'], expect={**OK, "value": contains(echo_head, '"method": "POST"', '"body_bytes": 8', '"target": "/echo"')})
    execute("execute/put-empty-body-argument", ["PUT", "{A}/echo", ""], expect={**OK, "value": contains(echo_head, '"method": "PUT"', '"body_bytes": 0')})
    execute("execute/patch-two-arguments-empty-body", ["patch", "{A}/echo"], expect={**OK, "value": contains(echo_head, '"method": "PATCH"', '"body_bytes": 0')})
    execute("execute/custom-lowercase-method-unchanged", ["purge", "{A}/echo"], expect={**OK, "value": contains(echo_head, '"method": "purge"')})
    execute("execute/unicode-body-argument", ["POST", "{A}/echo", "h\u00e9llo \U0001f600"], expect={**OK, "value": contains(echo_head, '"method": "POST"', '"body_bytes": 11')})
    execute("execute/redirect-followed", ["GET", "{A}/redir?status=302&to=/text"], expect={**OK, "value": text})
    execute("execute/redirect-chain-11", ["GET", "{A}/chain?n=11"],
            expect={**OK, "value": "302 {A}/chain?n=1\nLocation: /chain?n=0\nContent-Type: text/plain; charset=utf-8\nContent-Length: 12\nConnection: close\n\nredirecting\n"})
    execute("execute/post-redirect-not-followed", ["POST", "{A}/redir?status=303&to=/text", "x"],
            expect={**OK, "value": "303 {A}/redir?status=303&to=/text\nLocation: /text\nContent-Type: text/plain; charset=utf-8\nContent-Length: 12\nConnection: close\n\nredirecting\n"})
    execute("execute/response-headers-order", ["GET", "{A}/headers"], expect={**OK, "value": "200 {A}/headers\nX-Zeta: z1\nX-Alpha: a1\nSet-Cookie: a=1\nX-Dup: first\nSet-Cookie: b=2\nx-dup: second\nX-Empty: \nX-Spaces: value  with   inner  spaces\nContent-Type: text/plain; charset=utf-8\nContent-Length: 2\nConnection: close\n\nok"})
    execute("execute/chunked-response", ["GET", "{A}/chunked"], expect={**OK, "value": "200 {A}/chunked\nContent-Type: text/plain; charset=utf-8\nTransfer-Encoding: chunked\nConnection: close\n\nchunk-1;chunk-2;chunk-3"})
    execute("execute/binary-body", ["GET", "{A}/binary?hex=6361ff"], expect={**OK, "value": "200 {A}/binary?hex=6361ff\nContent-Type: text/plain; charset=utf-8\nContent-Length: 3\nConnection: close\n\nca\ufffd"})
    execute("execute/connection-dropped", ["GET", "{A}/drop"], expect=NETWORK)
    execute("execute/connection-refused", ["GET", "{CLOSED}/text"], expect=NETWORK)
    execute("execute/status-600", ["GET", "{A}/status?code=600"], expect=NETWORK)
    execute("execute/truncated-body", ["GET", "{A}/drop-mid-body"], expect=NETWORK)
    execute("execute/ftp-url", ["GET", "ftp://{N_HOST}/x"], expect=INVALID)
    execute("execute/empty-url", ["GET", ""], expect=INVALID)
    execute("execute/no-host-url", ["GET", "http://"], expect=INVALID)
    execute("execute/url-with-space", ["GET", "{N}/a b"], expect=INVALID)
    execute("execute/url-with-non-ascii", ["GET", "{N}/caf\u00e9"], expect=INVALID)
    execute("execute/invalid-method", ["GET X", "{N}/text"], expect=INVALID)
    execute("execute/invalid-method-emoji", ["\U0001f600", "{N}/text"], expect=INVALID)
    execute("execute/invalid-method-long-s", ["Po\u017fT", "{N}/text"], expect=INVALID)
    execute("execute/zero-arguments", [], expect=INVALID_ARGS)
    execute("execute/one-argument", ["GET"], expect=INVALID_ARGS)
    execute("execute/four-arguments", ["GET", "{N}/text", "b", "c"], expect=INVALID_ARGS)
    execute("execute/one-argument-invalid-method", ["GET X"], expect=INVALID_ARGS)
    execute("execute/four-arguments-invalid-method", ["GET X", "{N}/text", "b", "c"], expect=INVALID_ARGS)


# ---- listeners that exist only on some machines ------------------------------------------------------------------


def group_ipv6():
    rules("listeners")
    tag = ["ipv6"]
    send("send_request/ipv6-host-header-keeps-brackets", url="{V6}/echo", tags=tag,
         expect=echo(host="{V6_HOST}", target="/echo", url="{V6}/echo"), note="an IPv6 literal keeps its brackets in Host, with the non-default port")
    send("send_request/ipv6-userinfo-and-fragment", url="http://u:p@{V6_HOST}/echo?x#f", tags=tag,
         expect=echo(host="{V6_HOST}", target="/echo?x", url="http://u:p@{V6_HOST}/echo?x#f", hdr={"authorization": ABSENT}))
    send("send_request/ipv6-redirect-same-origin-keeps-headers", url="{V6}/redir?status=302&to=/echo", headers=CREDS_NO_HOST, tags=tag,
         expect=echo(url="{V6}/echo", hdr={**KEPT_ALL, "host": ["{V6_HOST}"]}))
    send("send_request/ipv6-redirect-absolute-same-origin", url="{V6}/redir?status=302&to={V6}/echo", headers=CREDS_NO_HOST, tags=tag,
         expect=echo(url="{V6}/echo", hdr={**KEPT_ALL, "host": ["{V6_HOST}"]}))
    send("send_request/ipv6-redirect-cross-origin-from-ipv4", url="{A}/redir?status=302&to={V6}/echo", headers=CREDS, tags=tag,
         expect=echo(url="{V6}/echo", hdr=stripped("{V6_HOST}")))
    send("send_request/ipv6-redirect-cross-origin-to-ipv4", url="{V6}/redir?status=302&to={A}/echo", headers=CREDS, tags=tag,
         expect=echo(url="{A}/echo", hdr=stripped("{A_HOST}")))
    send("send_request/ipv6-redirect-scheme-relative-authority", url="{A}/redir?status=302&to=//{V6_HOST}/echo", headers=CREDS_NO_HOST, tags=tag,
         expect=echo(url="{V6}/echo", hdr=stripped("{V6_HOST}")))
    send("send_request/ipv6-relative-location-resolution", url="{V6}/dir/sub/redir?status=302&to=../echo", tags=tag,
         expect=echo(url="{V6}/dir/echo", target="/dir/echo"))


def group_port80():
    rules("listeners")
    tag = ["port80"]
    note = "127.0.0.1:80 is reachable only where the port can be bound (a private network namespace); see README.md"
    for ident, url, host in [
        ("explicit-default-port", "http://127.0.0.1:80/echo", "127.0.0.1"), ("implicit-default-port", "http://127.0.0.1/echo", "127.0.0.1"),
        ("explicit-default-port-uppercase-host", "http://LOCALHOST:80/echo", "LOCALHOST"),
        ("explicit-default-port-with-userinfo", "http://u:p@127.0.0.1:80/echo", "127.0.0.1"),
    ]:
        assert host_header(url) == host
        send(f"send_request/host-{ident}", url=url, tags=tag, expect=echo(host=host, target="/echo", url=url),
             note="Host carries :port only for a port other than the scheme default; Response.url keeps the URL as given")
    send("send_request/host-explicit-default-port-caller-host-header", url="http://127.0.0.1:80/echo", headers=[("Host", "custom.example:80")], tags=tag,
         expect=echo(host="custom.example:80"), note=note)
    for ident, url, final, keep in [
        ("explicit-to-implicit", "http://127.0.0.1:80/redir?status=302&to=http://127.0.0.1/echo", "http://127.0.0.1/echo", True),
        ("implicit-to-explicit", "http://127.0.0.1/redir?status=302&to=http://127.0.0.1:80/echo", "http://127.0.0.1:80/echo", True),
        ("relative-location", "http://127.0.0.1:80/redir?status=302&to=/echo", "http://127.0.0.1:80/echo", True),
        ("host-case-and-default-port", "http://localhost/redir?status=302&to=http://LOCALHOST:80/echo", "http://LOCALHOST:80/echo", True),
        ("to-other-host-name", "http://127.0.0.1:80/redir?status=302&to=http://localhost/echo", "http://localhost/echo", False),
        ("from-ephemeral-port", "{A}/redir?status=302&to=http://127.0.0.1/echo", "http://127.0.0.1/echo", False),
        ("scheme-relative-from-ephemeral-port", "{A}/redir?status=302&to=//127.0.0.1/echo", "http://127.0.0.1/echo", False),
    ]:
        assert (origin(concrete(url)) == origin(final)) == keep, (ident, "the oracle disagrees with the intended origin comparison")
        host = host_header(final)
        expected = {**KEPT_ALL, "host": [host]} if keep else stripped(host)
        send(f"send_request/redirect-origin-default-port-{ident}", url=url, headers=CREDS_NO_HOST, tags=tag,
             expect=echo(url=final, hdr=expected), note="the port is compared after applying the scheme default (80 for http)")


GROUPS = [
    group_parse_method, group_parse_arguments, group_render_response, group_violations, group_invalid_request, group_url_characters,
    group_target_and_host, group_exchanges, group_redirects, group_origins, group_resolution, group_invalid_locations, group_decoding,
    group_failures, group_execute, group_ipv6, group_port80,
    *DECISION_GROUPS,
]


def build_cases() -> list[dict]:
    casekit.reset()
    for group in GROUPS:
        group()
    return list(casekit.CASES)


def summary(cases: list[dict]) -> str:
    by_rule = Counter(case.get("rule", "") for case in cases)
    functions = Counter(case["fn"] for case in cases)
    tags = Counter(tag for case in cases for tag in case.get("tags", ()))
    lines = [f"{len(cases)} cases, each with a contract expectation; by function {dict(functions)}; tags {dict(tags)}"]
    lines += [f"  {rule or '(none)':18s} {count}" for rule, count in sorted(by_rule.items(), key=lambda item: (item[0][:1] != 'R', item[0][:1] != 'D', item[0].zfill(4), item[0]))]
    return "\n".join(lines)


if __name__ == "__main__":
    built = build_cases()
    if len(sys.argv) > 2 and sys.argv[1] == "--write":
        with open(sys.argv[2], "w", encoding="ascii") as handle:
            json.dump(built, handle, ensure_ascii=True, indent=None)
    elif "--list" in sys.argv:
        for entry in built:
            print(entry["id"], entry.get("tags", ""))
    else:
        print(summary(built))
