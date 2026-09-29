"""Building blocks of the case table: the registry, the builders and the assertion helpers shared by cases.py (contract
rules R1-R7 and the general behavior) and decisions.py (decisions D1-D14).

A case is a dict: ``id`` (unique, ``fn/...``), ``fn``, the inputs of that function, ``expect`` (assertions over the
normalized result, see README.md; every case has one and both implementations must meet it) and optionally ``rule``
(the contract rule or decision it exercises, e.g. ``R4`` or ``D12``; groups set a default with ``rules()``), ``tags``
(``slow``; ``ipv6``, ``port80``, ``port65535`` for cases that need a listener some machines cannot provide),
``deadline_s``, ``body_digest`` and ``note``.
"""

from __future__ import annotations

import re
import string

from oracle import STAND_INS, followable, parse, recompose, request_target, resolve_ref

CASES: list[dict] = []
_IDS: set[str] = set()
_RULE = [""]  # the rule label new cases get unless they pass rule=

ABSENT = {"$absent": True}
OK = {"tag": "Ok"}
INVALID = {"tag": "Err", "error.variant": "InvalidRequest"}
NETWORK = {"tag": "Err", "error.variant": "NetworkFailed"}
INVALID_ARGS = {"tag": "Err", "error.variant": "InvalidArguments"}
VIOLATION = {"tag": "Violation", "phase": "validation"}

STANDARD = ["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
TCHAR_PUNCT = "!#$%&'*+-.^_`|~"
TCHARS = string.ascii_letters + string.digits + TCHAR_PUNCT
LIMIT = 67108864

CREDS = [("Authorization", "Bearer s3cret"), ("Cookie", "sid=1"), ("Proxy-Authorization", "Basic eHl6"), ("Host", "custom.example"), ("X-Keep", "yes")]
CREDS_NO_HOST = [header for header in CREDS if header[0] != "Host"]
KEPT_ALL = {"authorization": ["Bearer s3cret"], "cookie": ["sid=1"], "proxy-authorization": ["Basic eHl6"], "x-keep": ["yes"]}


# ---- registry -------------------------------------------------------------------------------------------------


def reset() -> None:
    CASES.clear()
    _IDS.clear()
    _RULE[0] = ""


def rules(label: str) -> None:
    """The rule label of the cases added from now on (until the next call)."""
    _RULE[0] = label


def add(ident, fn, *, rule=None, tags=(), expect=None, note=None, deadline=None, digest=False, **inputs):
    assert ident not in _IDS, f"duplicate case id {ident}"
    assert ident.split("/", 1)[0] == fn, f"case id {ident} must start with {fn}/"
    assert expect, f"{ident}: every case needs an expectation derived from the contract"
    _IDS.add(ident)
    case = {"id": ident, "fn": fn, **inputs}
    if rule or _RULE[0]:
        case["rule"] = rule or _RULE[0]
    if digest:
        case["body_digest"] = True
    if deadline:
        case["deadline_s"] = deadline
    if tags:
        case["tags"] = list(tags)
    case["expect"] = expect
    if note:
        case["note"] = note
    CASES.append(case)


def custom(name):
    return {"variant": "Custom", "name": name}


def send(ident, method="Get", url="{A}/text", headers=(), body="", timeout=5000, **kw):
    request = {"method": method, "url": url, "headers": [list(h) for h in headers], "body": body, "timeout_ms": timeout}
    add(ident, "send_request", request=request, **kw)


def execute(ident, arguments, **kw):
    add(ident, "execute", arguments=arguments, **kw)


def render(ident, status=200, url="http://api.example/", headers=(), body="", **kw):
    add(ident, "render_response", response={"status": status, "url": url, "headers": [list(h) for h in headers], "body": body}, **kw)


def cp(text):
    return "-".join(f"U+{ord(ch):04X}" for ch in text)


# ---- assertions -----------------------------------------------------------------------------------------------


def contains(*parts):
    """Assertion for a string result: every part occurs in it."""
    return {"$contains": list(parts)}


def ok(**fields):
    """ok(status=200, url=..., body=...) -> assertions on an Ok response."""
    return {"tag": "Ok", **{f"value.{key}": value for key, value in fields.items()}}


def std_headers(length, *, first=(), ctype="text/plain; charset=utf-8"):
    """The Response.headers of a ``respond()`` answer of the fixture server (see server.py), after optional leading fields."""
    fields = [{"name": name, "value": value} for name, value in first]
    return fields + [{"name": "Content-Type", "value": ctype}, {"name": "Content-Length", "value": str(length)}, {"name": "Connection", "value": "close"}]


def echo(*, method=None, version=None, target=None, host=None, hdr=None, body=None, body_bytes=None, order=None,
         order_no_host=None, url=None, status=200, extra=None):
    """Assertions on the ``echo`` route's JSON body (see server.py) and the response around it."""
    expect = {"tag": "Ok", "value.status": status}
    if url is not None:
        expect["value.url"] = url

    def put(key, value):
        expect["value.body.@json." + key] = value

    if method is not None:
        put("method", method)
    if version is not None:
        put("version", version)
    if target is not None:
        put("target", target)
    if host is not None:
        put("headers.host", [host])
    for name, values in (hdr or {}).items():
        put("headers." + name, values)
    if body is not None:
        put("body", body)
    if body_bytes is not None:
        put("body_bytes", body_bytes)
    if order is not None:
        put("order", order)
    if order_no_host is not None:
        put("order_no_host", order_no_host)
    if extra:
        expect.update(extra)
    return expect


def stripped(new_host, kept=("x-keep", ["yes"])):
    """The credential rule applied: the four headers gone, Host replaced by the URL's own, others kept."""
    return {"host": [new_host], kept[0]: kept[1], "authorization": ABSENT, "cookie": ABSENT, "proxy-authorization": ABSENT}


# ---- URLs -----------------------------------------------------------------------------------------------------


def pct(text, safe=""):
    out = []
    for ch in text:
        if ch.isascii() and (ch.isalnum() or ch in "-._~" or ch in safe):
            out.append(ch)
        else:
            out.extend(f"%{byte:02X}" for byte in ch.encode("utf-8"))
    return "".join(out)


_PLACEHOLDER = re.compile(r"(\{[A-Z0-9_]+\})")


def enc(text, safe=":/"):
    """Percent-encode a query value for use in a case URL, leaving {PLACEHOLDER} tokens for the drivers."""
    return "".join(part if _PLACEHOLDER.fullmatch(part) else pct(part, safe) for part in _PLACEHOLDER.split(text))


def concrete(text):
    return STAND_INS.concrete(text)


def place(text):
    return STAND_INS.abstract(text)


def resolved(base, reference):
    """(final URL as placeholder text, the resolved reference) for a case URL and a Location value."""
    target = resolve_ref(parse(concrete(base)), parse(concrete(reference)))
    return place(recompose(target)), target


def mirror(ident, ref, at=None, more=()):
    headers = [("X-Mirror", "ref=" + ref), ("X-Mirror-Id", ident)]
    if at:
        headers.append(("X-Mirror-At", at))
    return headers + list(more)


def alternating(text, upper_first):
    return "".join(ch.upper() if (index % 2 == 0) == upper_first else ch.lower() for index, ch in enumerate(text))


def redir(path, ref, status=302, extra=""):
    return f"{{A}}{path}?status={status}&to={enc(ref)}{extra}"


def followed_echo(ident, url, ref, headers=(), **kw):
    """A followed redirect answered by the echo route; every expectation comes from the oracle."""
    final, target = resolved(url, ref)
    assert followable(target), (url, ref)
    wire = request_target(concrete(final))
    assert wire != request_target(concrete(url)), f"{ident}: the resolved target equals the base's; use mirror()"
    send(ident, url=url, headers=list(headers) + [("X-Echo", "1")], expect=echo(target=wire, url=final), **kw)
