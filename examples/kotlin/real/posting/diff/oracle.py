#!/usr/bin/env python3
"""Independent oracles for the posting contract (client.cott, send_request rules and decisions D1-D14).

Every function transcribes the document it names: RFC 3986 (section 3.1 character classes, section 5.2 reference
resolution, section 5.3 recomposition, appendix B parsing), the Unicode Standard section 3.9 (Table 3-7 well-formed
byte sequences, Table 3-8 maximal-subpart replacement) and the contract text (URL characters, request target with
dot-segment removal, Host and port rules, origin comparison, received header lines and chunk-size lines).
Nothing here imports urllib.parse, http.client or any implementation under test, so an expectation computed with
these functions can disagree with an implementation, which is the point.

Running this file executes the self-tests: the RFC 3986 section 5.4 example tables and the two worked
remove_dot_segments examples of section 5.2.4, Unicode Table 3-8, and randomized comparisons of the UTF-8 decoder and
of the header-value rule with CPython's codecs (a guard against a transcription slip in this file, never a source of
expected values).
"""

from __future__ import annotations

import random
import re
import string
from dataclasses import dataclass

# ---- placeholders ---------------------------------------------------------------------------------------------


class Placeholders:
    """Maps ``{A}``-style placeholders to concrete origins and back.

    Case files and expectations only ever hold placeholders; a run substitutes the servers' ephemeral origins.
    """

    ORIGINS = ("A", "B", "N", "V6")  # {A} = http://127.0.0.1:PORT, {A_HOST} = 127.0.0.1:PORT, {A_PORT} = PORT
    PORTS = ("A", "B", "N", "V6", "CLOSED")

    def __init__(self, variables: dict[str, str]) -> None:
        self.variables = variables
        origins = [(variables[key], "{" + key + "}") for key in self.ORIGINS if key in variables]
        if "CLOSED" in variables:
            origins.append((variables["CLOSED"], "{CLOSED}"))
        hosts = [(variables[key + "_HOST"], "{" + key + "_HOST}") for key in self.ORIGINS if key + "_HOST" in variables]
        self._literals = origins + hosts  # origins first: an origin contains its host
        # ":041317" -> ":0{A_PORT}": leading zeros survive, so a client that shows them in Host or Response.url is caught
        self._ports = [
            (re.compile(":(0*)" + re.escape(variables[key + "_PORT"]) + r"(?!\d)"), ":\\g<1>{" + key + "_PORT}")
            for key in self.PORTS
            if key + "_PORT" in variables
        ]

    def concrete(self, text: str) -> str:
        for key, value in self.variables.items():
            text = text.replace("{" + key + "}", value)
        return text

    def abstract(self, value):
        """Recursively replace this run's origins in strings by their placeholders."""
        if isinstance(value, str):
            for needle, placeholder in self._literals:
                value = value.replace(needle, placeholder)
            for pattern, placeholder in self._ports:
                value = pattern.sub(placeholder, value)
            return value
        if isinstance(value, list):
            return [self.abstract(item) for item in value]
        if isinstance(value, dict):
            return {key: self.abstract(item) for key, item in value.items()}
        return value


#: Stand-in origins the case generator computes with; they never appear in a case file.
STAND_INS = Placeholders(
    {
        "A": "http://127.0.0.1:41001", "A_HOST": "127.0.0.1:41001", "A_PORT": "41001",
        "B": "http://127.0.0.1:41002", "B_HOST": "127.0.0.1:41002", "B_PORT": "41002",
        "N": "http://127.0.0.1:41003", "N_HOST": "127.0.0.1:41003", "N_PORT": "41003",
        "V6": "http://[::1]:41004", "V6_HOST": "[::1]:41004", "V6_PORT": "41004",
        "CLOSED": "http://127.0.0.1:41005", "CLOSED_PORT": "41005",
    }
)

# ---- rule 1: the URL characters -------------------------------------------------------------------------------

UNRESERVED = frozenset(string.ascii_letters + string.digits + "-._~")
GEN_DELIMS = frozenset(":/?#[]@")
SUB_DELIMS = frozenset("!$&'()*+,;=")
URL_CHARS = UNRESERVED | GEN_DELIMS | SUB_DELIMS  # "%" is valid only as %HH
HEX_DIGITS = frozenset("0123456789abcdefABCDEF")
#: The printable ASCII characters the contract names as invalid: < > " { } | backslash ^ and the grave accent.
INVALID_PRINTABLE = "".join(chr(code) for code in range(0x21, 0x7F) if chr(code) not in URL_CHARS and chr(code) != "%")
VALID_PRINTABLE = "".join(sorted(URL_CHARS, key=ord))


def url_characters_valid(text: str) -> bool:
    """Contract rule 1: only URL characters, and every "%" followed by two hexadecimal digits."""
    index, length = 0, len(text)
    while index < length:
        char = text[index]
        if char == "%":
            if index + 2 >= length or text[index + 1] not in HEX_DIGITS or text[index + 2] not in HEX_DIGITS:
                return False
            index += 3
        elif char in URL_CHARS:
            index += 1
        else:
            return False
    return True


# ---- RFC 3986 -------------------------------------------------------------------------------------------------

_APPENDIX_B = re.compile(r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?$", re.DOTALL)
DEFAULT_PORTS = {"http": 80, "https": 443}


@dataclass(frozen=True)
class Ref:
    """A parsed reference; ``None`` is "undefined" (separator absent), "" is "defined and empty"."""

    scheme: str | None
    authority: str | None
    path: str
    query: str | None
    fragment: str | None


def parse(text: str) -> Ref:
    match = _APPENDIX_B.match(text)
    assert match is not None  # the appendix B expression matches every string
    return Ref(match.group(2), match.group(4), match.group(5), match.group(7), match.group(9))


def recompose(ref: Ref) -> str:
    """RFC 3986 section 5.3."""
    out = ""
    if ref.scheme is not None:
        out += ref.scheme + ":"
    if ref.authority is not None:
        out += "//" + ref.authority
    out += ref.path
    if ref.query is not None:
        out += "?" + ref.query
    if ref.fragment is not None:
        out += "#" + ref.fragment
    return out


def remove_dot_segments(path: str) -> str:
    """RFC 3986 section 5.2.4, the two-buffer method, step for step."""
    inp, out = path, ""
    while inp:
        if inp.startswith("../"):  # 2A
            inp = inp[3:]
        elif inp.startswith("./"):  # 2A
            inp = inp[2:]
        elif inp.startswith("/./"):  # 2B
            inp = "/" + inp[3:]
        elif inp == "/.":  # 2B
            inp = "/"
        elif inp.startswith("/../"):  # 2C
            inp = "/" + inp[4:]
            out = out[: out.rfind("/")] if "/" in out else ""
        elif inp == "/..":  # 2C
            inp = "/"
            out = out[: out.rfind("/")] if "/" in out else ""
        elif inp in (".", ".."):  # 2D
            inp = ""
        else:  # 2E: move the first segment, with its initial "/", to the output
            start = 1 if inp.startswith("/") else 0
            end = inp.find("/", start)
            end = len(inp) if end == -1 else end
            out += inp[:end]
            inp = inp[end:]
    return out


def merge(base: Ref, reference_path: str) -> str:
    """RFC 3986 section 5.2.3."""
    if base.authority is not None and base.path == "":
        return "/" + reference_path
    cut = base.path.rfind("/")
    return (base.path[: cut + 1] if cut != -1 else "") + reference_path


def resolve_ref(base: Ref, ref: Ref) -> Ref:
    """RFC 3986 section 5.2.2, strict (a reference with a scheme is always absolute)."""
    if ref.scheme is not None:
        return Ref(ref.scheme.lower(), ref.authority, remove_dot_segments(ref.path), ref.query, ref.fragment)  # D4: RFC 3986 6.2.2.1
    if ref.authority is not None:
        return Ref(base.scheme, ref.authority, remove_dot_segments(ref.path), ref.query, ref.fragment)
    if ref.path == "":
        query = ref.query if ref.query is not None else base.query
        return Ref(base.scheme, base.authority, base.path, query, ref.fragment)
    if ref.path.startswith("/"):
        path = remove_dot_segments(ref.path)
    else:
        path = remove_dot_segments(merge(base, ref.path))
    return Ref(base.scheme, base.authority, path, ref.query, ref.fragment)


def resolve(base: str, reference: str) -> str:
    return recompose(resolve_ref(parse(base), parse(reference)))


def split_authority(authority: str) -> tuple[str | None, str, str | None]:
    """(userinfo, host as written, port digits or None); an IPv6 literal keeps its brackets."""
    userinfo, at, hostport = authority.rpartition("@")
    if not at:
        userinfo_out: str | None = None
    else:
        userinfo_out = userinfo
    if hostport.startswith("["):
        close = hostport.find("]")
        host, rest = hostport[: close + 1], hostport[close + 1 :]
        port = rest[1:] if rest.startswith(":") else None
    else:
        host, colon, port_text = hostport.partition(":")
        port = port_text if colon else None
    return userinfo_out, host, (port if port else None)


def port_state(port: str | None) -> tuple[str, int | None]:
    """D12: ("default", None) for an absent or empty port, ("ok", value) for a run of ASCII digits whose decimal value is
    at most 65535 (leading zeros allowed), ("invalid", None) for anything else."""
    if not port:
        return "default", None
    if not all(ch in "0123456789" for ch in port):
        return "invalid", None
    value = int(port)  # digits only, and Python integers do not overflow
    return ("ok", value) if value <= 65535 else ("invalid", None)


def unusable_port(url: str) -> bool:
    """D12: the URL has a port that is not a run of digits or above 65535 (InvalidRequest, never connects)."""
    ref = parse(url)
    return ref.authority is not None and port_state(split_authority(ref.authority)[2])[0] == "invalid"


def followable(target: Ref) -> bool:
    """Rule 4 and D12: a Location resolving to something not http(s), without a host or with an unusable port is not followed."""
    if target.scheme is None or target.scheme.lower() not in DEFAULT_PORTS or target.authority is None:
        return False
    _, host, port = split_authority(target.authority)
    return host != "" and port_state(port)[0] != "invalid"


def request_target(url: str) -> str:
    """Rule 2 and D3: the path with its literal "." and ".." segments removed by RFC 3986 5.2.4 ("/" when empty), then "?" and
    the query when one is present before any "#"; percent-encoded dots stay."""
    ref = parse(url)
    return (remove_dot_segments(ref.path) or "/") + ("?" + ref.query if ref.query is not None else "")


def host_header(url: str) -> str:
    """Rule 3 and D12: the host as written, plus ":port" (decimal value, no leading zeros) only when the port differs from
    the scheme default; an empty port is the default."""
    ref = parse(url)
    assert ref.scheme is not None and ref.authority is not None
    _, host, port = split_authority(ref.authority)
    state, value = port_state(port)
    assert state != "invalid", f"{url}: not a requestable port"
    return host if value is None or value == DEFAULT_PORTS[ref.scheme.lower()] else f"{host}:{value}"


def origin(url: str) -> tuple[str, str, int]:
    """Rule 5 and D12: scheme and host ASCII case-insensitive, the port as its decimal value after applying the scheme default."""
    ref = parse(url)
    assert ref.scheme is not None and ref.authority is not None
    _, host, port = split_authority(ref.authority)
    state, value = port_state(port)
    assert state != "invalid", f"{url}: not a requestable port"
    return ref.scheme.lower(), host.lower(), value if value is not None else DEFAULT_PORTS[ref.scheme.lower()]


# ---- rule 6: UTF-8 decoding ------------------------------------------------------------------------------------


def decode_utf8(data: bytes, strict: bool = False) -> str:
    """Unicode 3.9: replace each maximal subpart of an ill-formed sequence by one U+FFFD (Table 3-7 / 3-8); with
    ``strict`` an ill-formed sequence raises ValueError instead."""
    out: list[str] = []
    index, length = 0, len(data)
    while index < length:
        lead = data[index]
        if lead <= 0x7F:
            out.append(chr(lead))
            index += 1
            continue
        if 0xC2 <= lead <= 0xDF:
            follow, low, high = 1, 0x80, 0xBF
        elif lead == 0xE0:
            follow, low, high = 2, 0xA0, 0xBF
        elif lead == 0xED:
            follow, low, high = 2, 0x80, 0x9F
        elif 0xE1 <= lead <= 0xEF:  # E1..EC and EE..EF
            follow, low, high = 2, 0x80, 0xBF
        elif lead == 0xF0:
            follow, low, high = 3, 0x90, 0xBF
        elif 0xF1 <= lead <= 0xF3:
            follow, low, high = 3, 0x80, 0xBF
        elif lead == 0xF4:
            follow, low, high = 3, 0x80, 0x8F
        else:  # 80..C1 and F5..FF never start a well-formed sequence
            if strict:
                raise ValueError(f"ill-formed UTF-8 at byte {index}")
            out.append("\ufffd")
            index += 1
            continue
        end = index + 1
        complete = True
        for position in range(follow):
            lo, hi = (low, high) if position == 0 else (0x80, 0xBF)
            if end >= length or not lo <= data[end] <= hi:
                complete = False
                break
            end += 1
        if complete:
            code = lead & (0x1F if follow == 1 else 0x0F if follow == 2 else 0x07)
            for byte in data[index + 1 : end]:
                code = (code << 6) | (byte & 0x3F)
            out.append(chr(code))
        else:
            if strict:
                raise ValueError(f"ill-formed UTF-8 at byte {index}")
            out.append("\ufffd")  # the bytes consumed so far are one maximal subpart
        index = end
    return "".join(out)


# ---- decisions D5, D6, D14 and D10: received header lines and chunk-size lines ------------------------------------

#: HTTP token characters (RFC 9110 tchar, what real.posting.client.parse_method calls a token): ALPHA, DIGIT and !#$%&'*+-.^_`|~
TOKEN_BYTES = frozenset((string.ascii_letters + string.digits + "!#$%&'*+-.^_`|~").encode())


def trim_ows(value: bytes) -> bytes:
    """D5: leading and trailing SP and HTAB removed."""
    return value.strip(b" \t")


def field_line(line: bytes) -> tuple[str, bytes] | None:
    """D14 and D5: the (name, value) of a received header line, or None when it is not a field line (NetworkFailed).  The
    name is one or more token characters immediately followed by ":", it is kept as received; the value is what follows the
    first ":" without its leading and trailing SP/HTAB."""
    name, colon, value = line.partition(b":")
    if not colon or not name or any(byte not in TOKEN_BYTES for byte in name):
        return None
    return name.decode("ascii"), trim_ows(value)


def valid_block(lines: list[bytes]) -> bool:
    """D14: every received header line is a field line (otherwise the response is NetworkFailed)."""
    return all(field_line(line) is not None for line in lines)


def decode_values(values: list[bytes]) -> list[str]:
    """D6: the values of the final response's header block are decoded as a whole: all ASCII -> as is; otherwise all valid
    UTF-8 -> UTF-8; otherwise every value ISO-8859-1.  (Names are tokens, hence ASCII.)"""
    if all(byte < 0x80 for value in values for byte in value):
        decode = decode_utf8
    else:
        try:
            for value in values:
                decode_utf8(value, strict=True)
            decode = decode_utf8
        except ValueError:
            def decode(value: bytes) -> str:
                return "".join(chr(byte) for byte in value)
    return [decode(value) for value in values]


def expected_headers(lines: list[bytes]) -> list[dict]:
    """The Response.headers a client must report for these received header lines (D14 names, D5 trimming, D6 decoding of
    the values); the lines must be a valid block."""
    fields = [field_line(line) for line in lines]
    assert all(field is not None for field in fields), f"not a valid header block: {lines!r}"
    values = decode_values([value for _, value in fields])
    return [{"name": name, "value": value} for (name, _), value in zip(fields, values)]


HEX_BYTES = frozenset(b"0123456789abcdefABCDEF")


def chunk_size_line(line: bytes) -> int | None:
    """D10: the value of a received chunk-size line (without its line end), or None when the line is NetworkFailed.  It
    starts with one or more hexadecimal digits; after them only nothing, SP/HTAB, or optional SP/HTAB followed by ";" and an
    ignored chunk extension may follow."""
    digits = 0
    while digits < len(line) and line[digits] in HEX_BYTES:
        digits += 1
    rest = line[digits:].lstrip(b" \t")
    if digits == 0 or not (rest == b"" or rest.startswith(b";")):
        return None
    return int(line[:digits], 16)


# ---- test vectors ----------------------------------------------------------------------------------------------

RFC_BASE = "http://a/b/c/d;p?q"
#: RFC 3986 section 5.4.1, verbatim.
RFC_NORMAL = [
    ("g:h", "g:h"), ("g", "http://a/b/c/g"), ("./g", "http://a/b/c/g"), ("g/", "http://a/b/c/g/"),
    ("/g", "http://a/g"), ("//g", "http://g"), ("?y", "http://a/b/c/d;p?y"), ("g?y", "http://a/b/c/g?y"),
    ("#s", "http://a/b/c/d;p?q#s"), ("g#s", "http://a/b/c/g#s"), ("g?y#s", "http://a/b/c/g?y#s"),
    (";x", "http://a/b/c/;x"), ("g;x", "http://a/b/c/g;x"), ("g;x?y#s", "http://a/b/c/g;x?y#s"),
    ("", "http://a/b/c/d;p?q"), (".", "http://a/b/c/"), ("./", "http://a/b/c/"), ("..", "http://a/b/"),
    ("../", "http://a/b/"), ("../g", "http://a/b/g"), ("../..", "http://a/"), ("../../", "http://a/"),
    ("../../g", "http://a/g"),
]
#: RFC 3986 section 5.4.2, verbatim (the strict answer for "http:g").
RFC_ABNORMAL = [
    ("../../../g", "http://a/g"), ("../../../../g", "http://a/g"), ("/./g", "http://a/g"), ("/../g", "http://a/g"),
    ("g.", "http://a/b/c/g."), (".g", "http://a/b/c/.g"), ("g..", "http://a/b/c/g.."), ("..g", "http://a/b/c/..g"),
    ("./../g", "http://a/b/g"), ("./g/.", "http://a/b/c/g/"), ("g/./h", "http://a/b/c/g/h"),
    ("g/../h", "http://a/b/c/h"), ("g;x=1/./y", "http://a/b/c/g;x=1/y"), ("g;x=1/../y", "http://a/b/c/y"),
    ("g?y/./x", "http://a/b/c/g?y/./x"), ("g?y/../x", "http://a/b/c/g?y/../x"), ("g#s/./x", "http://a/b/c/g#s/./x"),
    ("g#s/../x", "http://a/b/c/g#s/../x"), ("http:g", "http:g"),
]
#: Unicode Table 3-8: the bytes and the required U+FFFD substitution.
TABLE_3_8_BYTES = bytes.fromhex("61 F1 80 80 E1 80 C2 62 80 63 80 BF 64".replace(" ", ""))
TABLE_3_8_TEXT = "a\ufffd\ufffd\ufffdb\ufffdc\ufffd\ufffdd"


def self_test() -> None:
    assert INVALID_PRINTABLE == '"<>\\^`{|}' and len(INVALID_PRINTABLE) == 9, INVALID_PRINTABLE
    assert len(VALID_PRINTABLE) == 84, len(VALID_PRINTABLE)
    assert url_characters_valid("http://h:1/a%2Fb?x=1&y=%7e#f") and not url_characters_valid("a b")
    assert not url_characters_valid("%") and not url_characters_valid("%4") and not url_characters_valid("%4g")
    assert not url_characters_valid("\u00e9") and not url_characters_valid("a\x7f") and url_characters_valid("[::1]")

    for reference, want in RFC_NORMAL + RFC_ABNORMAL:
        got = resolve(RFC_BASE, reference)
        assert got == want, f"RFC 3986 example {reference!r}: {got!r} != {want!r}"
    assert remove_dot_segments("/a/b/c/./../../g") == "/a/g"  # the two worked examples of section 5.2.4
    assert remove_dot_segments("mid/content=5/../6") == "mid/6"
    assert resolve("http://h/dir/redir", "?q=1") == "http://h/dir/redir?q=1"  # the three examples in the contract's send_request doc
    assert resolve("http://h/redir", "../../echo") == "http://h/echo"
    assert resolve("http://h/a/b/c", "..//g") == "http://h/a//g"
    assert resolve("http://h", "g") == "http://h/g"  # merge with an empty base path
    assert resolve("http://h?x", "?y#z") == "http://h?y#z"
    assert resolve("http://h/p#base", "") == "http://h/p"  # the base fragment is not inherited
    assert resolve("http://h/p", "#") == "http://h/p#" and resolve("http://h/p", "?") == "http://h/p?"
    assert request_target("http://h") == "/" and request_target("http://h?") == "/?"
    assert request_target("http://h/p?#f") == "/p?" and request_target("http://h/p#f?x") == "/p"
    assert request_target("http://h/a/./b/../echo") == "/a/echo"  # D3: the contract's own example
    assert request_target("http://h/a/b/..") == "/a/" and request_target("http://h/a/b/.") == "/a/b/"
    assert request_target("http://h/..") == "/" and request_target("http://h/a//../x") == "/a/x"
    assert request_target("http://h/a/%2E%2E/x") == "/a/%2E%2E/x" and request_target("http://h/a/.../x") == "/a/.../x"
    assert request_target("http://h/a/../echo?x=/../y#/../z") == "/echo?x=/../y"
    assert host_header("http://U:p@LocalHost:80/x") == "LocalHost" and host_header("http://h:8080/") == "h:8080"
    assert host_header("https://[::1]:443/") == "[::1]" and host_header("http://[::1]:9/") == "[::1]:9"
    assert host_header("http://h:080/") == "h" and host_header("http://h:/") == "h"  # D12
    assert host_header("http://h:0000000000000080/") == "h" and host_header("http://h:08080/") == "h:8080"
    assert host_header("http://h:65535/") == "h:65535" and host_header("http://h:0/") == "h:0"
    assert [port_state(p) for p in (None, "", "80", "0080", "65535", "65536", "0065536", "abc", "+80", "8_0", "0x50", "８０")] == [
        ("default", None), ("default", None), ("ok", 80), ("ok", 80), ("ok", 65535), ("invalid", None), ("invalid", None),
        ("invalid", None), ("invalid", None), ("invalid", None), ("invalid", None), ("invalid", None)]
    assert port_state("9" * 40) == ("invalid", None) and port_state("0" * 40 + "41317") == ("ok", 41317)
    assert unusable_port("http://h:abc/") and unusable_port("http://[::1]:65536/") and not unusable_port("http://h:080/")
    assert origin("HTTP://H:80/x") == origin("http://h/y") and origin("http://h:81/") != origin("http://h/")
    assert origin("http://h:080/") == origin("http://h/") == origin("http://H:/") and origin("http://h:0081/") == origin("http://h:81/")
    assert not followable(parse("http:g")) and not followable(parse("http://")) and followable(parse("https://h"))
    assert not followable(parse("http://h:abc/")) and not followable(parse("http://h:65536/")) and followable(parse("http://h:0080/"))
    assert resolve("http://a/b", "HTTP://H/x/./y") == "http://H/x/y" and resolve("http://a/b", "hTTpS://h") == "https://h"  # D4
    assert resolve("http://a/b", "HTTP:g") == "http:g"

    assert decode_utf8(TABLE_3_8_BYTES) == TABLE_3_8_TEXT
    assert decode_utf8(bytes.fromhex("eda080")) == "\ufffd" * 3
    assert decode_utf8(bytes.fromhex("efbbbf7800")) == "\ufeffx\x00"  # BOM and NUL are kept
    rng = random.Random(3629)
    pool = [0x61, 0x00, 0x7F, 0x80, 0x8F, 0x90, 0x9F, 0xA0, 0xBF, 0xC0, 0xC1, 0xC2, 0xDF, 0xE0, 0xE1, 0xEC, 0xED,
            0xEE, 0xEF, 0xF0, 0xF1, 0xF3, 0xF4, 0xF5, 0xFF]
    for _ in range(30000):
        data = bytes(rng.choice(pool) for _ in range(rng.randint(0, 10)))
        assert decode_utf8(data) == data.decode("utf-8", "replace"), data.hex()
    for _ in range(20000):  # the strict decoder accepts exactly what CPython's strict decoder accepts
        data = bytes(rng.choice(pool) for _ in range(rng.randint(0, 6)))
        try:
            decode_utf8(data, strict=True)
            mine = True
        except ValueError:
            mine = False
        try:
            data.decode("utf-8")
            theirs = True
        except UnicodeDecodeError:
            theirs = False
        assert mine == theirs, data.hex()
    # D5, D6, D14 by hand
    assert trim_ows(b" \t a \t ") == b"a" and trim_ows(b"a \t b") == b"a \t b" and trim_ows(b"  \t ") == b""
    assert len(TOKEN_BYTES) == 77 and not TOKEN_BYTES & set(b" \"(),/:;<=>?@[\\]{}\x00\x01\t\x0b\x0c\x7f\x80\xff")  # RFC 9110: 62 + 15
    assert expected_headers([b"X-A:  a ", b"X-B:\t\tb\t"]) == [{"name": "X-A", "value": "a"}, {"name": "X-B", "value": "b"}]
    assert expected_headers([b"X-Utf8: caf\xc3\xa9"]) == [{"name": "X-Utf8", "value": "caf\u00e9"}]
    assert expected_headers([b"X-Latin1: caf\xe9", b"X-Utf8: caf\xc3\xa9"]) == [
        {"name": "X-Latin1", "value": "caf\u00e9"}, {"name": "X-Utf8", "value": "caf\u00c3\u00a9"}]
    assert expected_headers([b"X-S: \xed\xa0\x80"]) == [{"name": "X-S", "value": "\u00ed\u00a0\u0080"}]  # a UTF-8 surrogate is not valid UTF-8
    assert field_line(b"X:A: v") == ("X", b"A: v") and field_line(b"x:") == ("x", b"") and field_line(b"123: v") == ("123", b"v")
    assert field_line(b"!#$%&'*+-.^_`|~: v") == ("!#$%&'*+-.^_`|~", b"v")
    for bad in (b"X-A : v", b"X-A\t: v", b": v", b":", b"X@A: v", b"@: v", b"X-A", b"", b" X-A: v", b" folded", b"\tX-A: v", b"X-\xc3\xa9: v", b"X-\xe9: v",
                b"X A: v", b"X\x00A: v", b"X\x7fA: v", b"(X): v", b"X-A\r: v", b"\xef\xbb\xbfX-A: v"):
        assert field_line(bad) is None, bad
    assert valid_block([b"X-A: 1", b"X-B: 2"]) and not valid_block([b"X-A: 1", b"X@B: 2"]) and valid_block([])
    for _ in range(20000):  # D6 against the same rule spelled with CPython's codecs
        values = [bytes(rng.choice(pool) for _ in range(rng.randint(0, 4))) for _ in range(rng.randint(1, 3))]
        try:
            encoding = "ascii" if all(value.isascii() for value in values) else None
            if encoding is None:
                for value in values:
                    value.decode("utf-8")
                encoding = "utf-8"
        except UnicodeDecodeError:
            encoding = "latin-1"
        assert decode_values(values) == [value.decode(encoding) for value in values], values
    # D10: the chunk-size line
    assert [chunk_size_line(line) for line in (b"2", b"a", b"A", b"0002", b"1F", b"1f", b"0", b"00")] == [2, 10, 10, 2, 31, 31, 0, 0]
    for accepted in (b"2 ", b"2\t", b"2  ", b"2 \t ", b"2;a=b", b"2 ; a=b", b"2;a", b"2\t;a", b"2; a=b", b"2 ;a=b;c=d", b"2;a=\"b c\"", b"02 "):
        assert chunk_size_line(accepted) == 2, accepted
    for rejected in (b" 2", b"\t2", b"0x2", b"2g", b"+2", b"-2", b"2_0", b"2.0", b"", b";a", b" ;a", b"2 x", b"2\x0b", b"2\x0c", b"2 \x00", b"2\xc2\xa0", "\uff12".encode()):
        assert chunk_size_line(rejected) is None, rejected
    print("oracle self-tests passed")


if __name__ == "__main__":
    self_test()
