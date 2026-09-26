from typing import Final

_HEX: Final[str] = "0123456789abcdefABCDEF"
_DEC: Final[str] = "0123456789"


def _is_ipv4(text: str) -> bool:
    octets = text.split(".")
    if len(octets) != 4:
        return False
    for octet in octets:
        if not octet or len(octet) > 3 or any(ch not in _DEC for ch in octet):
            return False
        if len(octet) > 1 and octet[0] == "0":
            return False
        if int(octet) > 255:
            return False
    return True


def _is_hextet(text: str) -> bool:
    return 1 <= len(text) <= 4 and all(ch in _HEX for ch in text)


def _is_ipv6(text: str) -> bool:
    address = text
    if "%" in text:
        address, scope = text.split("%", 1)
        if not scope or "%" in scope:
            return False
    parts = address.split(":")
    if len(parts) < 3:
        return False
    if "." in parts[-1]:
        if not _is_ipv4(parts[-1]):
            return False
        parts = parts[:-1] + ["0", "0"]
    if address.count("::") > 1:
        return False
    if "::" in address:
        head, tail = address.split("::", 1)
        head_parts = head.split(":") if head else []
        tail_parts = tail.split(":") if tail else []
        if tail_parts and "." in tail_parts[-1]:
            tail_parts = tail_parts[:-1] + ["0", "0"]
        if any(not _is_hextet(p) for p in head_parts + tail_parts):
            return False
        return len(head_parts) + len(tail_parts) <= 7
    if any(not _is_hextet(p) for p in parts):
        return False
    return len(parts) == 8


def short_host_name(host: str) -> str:
    if _is_ipv4(host) or _is_ipv6(host):
        return host
    return host.split(",", 1)[0].split(".", 1)[0]
