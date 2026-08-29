from cott_runtime import Err, Nothing, Ok, Result, Some
from frogmouth.model_types import Location, LocationKind_Remote
from frogmouth.navigation_types import (
    NavigationError,
    NavigationError_InvalidLocation,
    NavigationError_UnsupportedScheme,
)


def resolve_absolute_location(value: str) -> Result[Location, NavigationError]:
    fragment_position = value.find("#")
    if fragment_position >= 0:
        target = value[:fragment_position]
        fragment_value = value[fragment_position + 1 :]
    else:
        target = value
        fragment_value = ""

    separator = target.find("://")
    if separator < 0:
        colon = target.find(":")
        if colon > 0:
            candidate_scheme = target[:colon]
            valid_scheme = candidate_scheme[0].isalpha() and candidate_scheme[0].isascii()
            for character in candidate_scheme[1:]:
                if not character.isascii() or (not character.isalnum() and character not in "+-."):
                    valid_scheme = False
                    break
            if valid_scheme:
                return Err(error=NavigationError_UnsupportedScheme(scheme=candidate_scheme.lower()))
        return Err(error=NavigationError_InvalidLocation(value=value))

    candidate_scheme = target[:separator]
    if not candidate_scheme or not candidate_scheme[0].isalpha() or not candidate_scheme[0].isascii():
        return Err(error=NavigationError_InvalidLocation(value=value))
    for character in candidate_scheme[1:]:
        if not character.isascii() or (not character.isalnum() and character not in "+-."):
            return Err(error=NavigationError_InvalidLocation(value=value))

    scheme = candidate_scheme.lower()
    if scheme != "http" and scheme != "https":
        return Err(error=NavigationError_UnsupportedScheme(scheme=scheme))

    for character in target:
        codepoint = ord(character)
        if codepoint <= 32 or codepoint >= 127:
            return Err(error=NavigationError_InvalidLocation(value=value))

    authority_start = separator + 3
    authority_end = len(target)
    for delimiter in "/?":
        position = target.find(delimiter, authority_start)
        if position >= 0 and position < authority_end:
            authority_end = position
    authority = target[authority_start:authority_end]
    if not authority:
        return Err(error=NavigationError_InvalidLocation(value=value))

    host_port = authority.rsplit("@", 1)[-1]
    if not host_port:
        return Err(error=NavigationError_InvalidLocation(value=value))

    port = ""
    if host_port.startswith("["):
        closing_bracket = host_port.find("]")
        if closing_bracket <= 1 or host_port.find("[", 1) >= 0 or host_port.find("]", closing_bracket + 1) >= 0:
            return Err(error=NavigationError_InvalidLocation(value=value))
        host = host_port[1:closing_bracket]
        suffix = host_port[closing_bracket + 1 :]
        if suffix:
            if not suffix.startswith(":"):
                return Err(error=NavigationError_InvalidLocation(value=value))
            port = suffix[1:]
            if not port:
                return Err(error=NavigationError_InvalidLocation(value=value))
        for character in host:
            if character not in "0123456789abcdefABCDEF:.%abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_":
                return Err(error=NavigationError_InvalidLocation(value=value))
    else:
        if "[" in host_port or "]" in host_port or host_port.count(":") > 1:
            return Err(error=NavigationError_InvalidLocation(value=value))
        if ":" in host_port:
            host, port = host_port.rsplit(":", 1)
            if not port:
                return Err(error=NavigationError_InvalidLocation(value=value))
        else:
            host = host_port
        if not host:
            return Err(error=NavigationError_InvalidLocation(value=value))
        for character in host:
            if not character.isalnum() and character != "." and character != "-":
                return Err(error=NavigationError_InvalidLocation(value=value))

    if port:
        for character in port:
            if character < "0" or character > "9":
                return Err(error=NavigationError_InvalidLocation(value=value))
        significant_port = port.lstrip("0")
        if len(significant_port) > 5 or (len(significant_port) == 5 and significant_port > "65535"):
            return Err(error=NavigationError_InvalidLocation(value=value))

    if fragment_value:
        fragment = Some(value=fragment_value)
    else:
        fragment = Nothing()
    return Ok(value=Location(kind=LocationKind_Remote(), target=target, fragment=fragment))
