from urllib.parse import unquote

from cott_runtime import Err, Ok, Result
from real.pgcli_types import ConnectionError, ConnectionError_InvalidDsn, ConnectionInputs


def _valid_percent_encoding(value: str) -> bool:
    index = 0
    while index < len(value):
        if value[index] == "%":
            if index + 2 >= len(value):
                return False
            high = value[index + 1]
            low = value[index + 2]
            high_valid = "0" <= high <= "9" or "a" <= high.casefold() <= "f"
            low_valid = "0" <= low <= "9" or "a" <= low.casefold() <= "f"
            if not high_valid or not low_valid:
                return False
            index += 3
        else:
            index += 1
    return True


def _parse_dsn_parts(value: str) -> tuple[bool, str, str, str, str, str]:
    separator = value.find("://")
    if separator <= 0:
        return (False, "", "", "", "", "")
    scheme = value[:separator].casefold()
    if scheme != "postgres" and scheme != "postgresql":
        return (False, "", "", "", "", "")

    remainder = value[separator + 3 :]
    slash = remainder.find("/")
    if slash < 0:
        return (False, "", "", "", "", "")
    authority = remainder[:slash]
    path_and_query = remainder[slash + 1 :]
    if "#" in path_and_query:
        return (False, "", "", "", "", "")
    query = path_and_query.find("?")
    database_encoded = path_and_query if query < 0 else path_and_query[:query]
    if database_encoded == "" or "/" in database_encoded:
        return (False, "", "", "", "", "")

    user = ""
    password = ""
    host_and_port = authority
    at = authority.rfind("@")
    if at >= 0:
        user_info = authority[:at]
        host_and_port = authority[at + 1 :]
        colon = user_info.find(":")
        if colon < 0:
            user_encoded = user_info
            password_encoded = ""
        else:
            user_encoded = user_info[:colon]
            password_encoded = user_info[colon + 1 :]
        if not _valid_percent_encoding(user_encoded) or not _valid_percent_encoding(password_encoded):
            return (False, "", "", "", "", "")
        user = unquote(user_encoded)
        password = unquote(password_encoded)

    host_encoded = ""
    port = ""
    if host_and_port.startswith("["):
        close = host_and_port.find("]")
        if close <= 1:
            return (False, "", "", "", "", "")
        host_encoded = host_and_port[1:close]
        suffix = host_and_port[close + 1 :]
        if suffix != "":
            if not suffix.startswith(":") or len(suffix) == 1:
                return (False, "", "", "", "", "")
            port = suffix[1:]
    else:
        if host_and_port.count(":") > 1:
            return (False, "", "", "", "", "")
        colon = host_and_port.rfind(":")
        if colon < 0:
            host_encoded = host_and_port
        else:
            host_encoded = host_and_port[:colon]
            port = host_and_port[colon + 1 :]
            if port == "":
                return (False, "", "", "", "", "")

    if not _valid_percent_encoding(host_encoded) or not _valid_percent_encoding(database_encoded):
        return (False, "", "", "", "", "")
    if port != "" and not _valid_percent_encoding(port):
        return (False, "", "", "", "", "")
    host = unquote(host_encoded)
    database = unquote(database_encoded)
    if database == "":
        return (False, "", "", "", "", "")
    return (True, host, unquote(port), user, password, database)


def parse_dsn(value: str) -> Result[ConnectionInputs, ConnectionError]:
    valid, host, port, user, password, database = _parse_dsn_parts(value)
    if not valid:
        return Err(error=ConnectionError_InvalidDsn(value=value))
    return Ok(value=ConnectionInputs(host=host, port=port, user=user, password=password, database=database))
