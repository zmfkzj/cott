#!/usr/bin/env python3
"""Independent oracles for the posting contract (client.cott, send_request rules).

Every function transcribes the document it names: RFC 3986 (section 3.1 character classes, section 5.2 reference
resolution, section 5.3 recomposition, appendix B parsing), the Unicode Standard section 3.9 (Table 3-7 well-formed
byte sequences, Table 3-8 maximal-subpart replacement) and the contract text.  Nothing here imports urllib.parse,
http.client or any implementation under test, so an expectation computed with these functions can disagree with an
implementation, which is the point.

Running this file executes the self-tests: the RFC 3986 section 5.4 example tables and the two worked
remove_dot_segments examples of section 5.2.4, Unicode Table 3-8, and a randomized comparison of the decoder with
CPython's (a guard against a transcription slip in this file, never a source of expected values).
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
    PORTS = ("A", "B", "V6")

    def __init__(self, variables: dict[str, str]) -> None:
        self.variables = variables
        origins = [(variables[key], "{" + key + "}") for key in self.ORIGINS if key in variables]
        if "CLOSED" in variables:
            origins.append((variables["CLOSED"], "{CLOSED}"))
        hosts = [(variables[key + "_HOST"], "{" + key + "_HOST}") for key in self.ORIGINS if key + "_HOST" in variables]
        self._literals = origins + hosts  # origins first: an origin contains its host
        self._ports = [
            (re.compile(":" + re.escape(variables[key + "_PORT"]) + r"(?!\d)"), ":{" + key + "_PORT}")
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
        "N": "http://127.0.0.1:41003", "N_HOST": "127.0.0.1:41003",
        "V6": "http://[::1]:41004", "V6_HOST": "[::1]:41004", "V6_PORT": "41004",
        "CLOSED": "http://127.0.0.1:41005",
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
DEFAULT_PORTS = {"http": "80", "https": "443"}


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
        return Ref(ref.scheme, ref.authority, remove_dot_segments(ref.path), ref.query, ref.fragment)
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


def followable(target: Ref) -> bool:
    """Rule 4: a Location resolving to something not http(s), or without a host, is not followed."""
    if target.scheme is None or target.scheme.lower() not in DEFAULT_PORTS or target.authority is None:
        return False
    return split_authority(target.authority)[1] != ""


def request_target(url: str) -> str:
    """Rule 2: the path ("/" when empty), then "?" and the query when one is present before any "#"."""
    ref = parse(url)
    return (ref.path or "/") + ("?" + ref.query if ref.query is not None else "")


def host_header(url: str) -> str:
    """Rule 3: the host as written, plus ":port" only for a port other than the scheme default."""
    ref = parse(url)
    assert ref.scheme is not None and ref.authority is not None
    _, host, port = split_authority(ref.authority)
    default = DEFAULT_PORTS[ref.scheme.lower()]
    return host if port is None or port == default else f"{host}:{port}"


def origin(url: str) -> tuple[str, str, str]:
    """Rule 5: scheme and host ASCII case-insensitive, the port after applying the scheme default."""
    ref = parse(url)
    assert ref.scheme is not None and ref.authority is not None
    _, host, port = split_authority(ref.authority)
    return ref.scheme.lower(), host.lower(), port if port is not None else DEFAULT_PORTS[ref.scheme.lower()]


# ---- rule 6: UTF-8 decoding ------------------------------------------------------------------------------------


def decode_utf8(data: bytes) -> str:
    """Unicode 3.9: replace each maximal subpart of an ill-formed sequence by one U+FFFD (Table 3-7 / 3-8)."""
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
            out.append("\ufffd")  # the bytes consumed so far are one maximal subpart
        index = end
    return "".join(out)


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
    assert host_header("http://U:p@LocalHost:80/x") == "LocalHost" and host_header("http://h:8080/") == "h:8080"
    assert host_header("https://[::1]:443/") == "[::1]" and host_header("http://[::1]:9/") == "[::1]:9"
    assert origin("HTTP://H:80/x") == origin("http://h/y") and origin("http://h:81/") != origin("http://h/")
    assert not followable(parse("http:g")) and not followable(parse("http://")) and followable(parse("https://h"))

    assert decode_utf8(TABLE_3_8_BYTES) == TABLE_3_8_TEXT
    assert decode_utf8(bytes.fromhex("eda080")) == "\ufffd" * 3
    assert decode_utf8(bytes.fromhex("efbbbf7800")) == "\ufeffx\x00"  # BOM and NUL are kept
    rng = random.Random(3629)
    pool = [0x61, 0x00, 0x7F, 0x80, 0x8F, 0x90, 0x9F, 0xA0, 0xBF, 0xC0, 0xC1, 0xC2, 0xDF, 0xE0, 0xE1, 0xEC, 0xED,
            0xEE, 0xEF, 0xF0, 0xF1, 0xF3, 0xF4, 0xF5, 0xFF]
    for _ in range(30000):
        data = bytes(rng.choice(pool) for _ in range(rng.randint(0, 10)))
        assert decode_utf8(data) == data.decode("utf-8", "replace"), data.hex()
    print("oracle self-tests passed")


if __name__ == "__main__":
    self_test()
