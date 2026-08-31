from urllib.parse import unquote

from cott_runtime import Err, Nothing, Ok, Option, Result, Some
from real.pgcli_types import (
    ConnectionError,
    ConnectionError_InvalidDsn,
    ConnectionError_InvalidPort,
    ConnectionError_MissingDatabase,
    ConnectionError_SshInvalid,
    ConnectionError_TlsInvalid,
    ConnectionInputs,
    ConnectionPlan,
    ConnectionProfile,
    ConnectionRequest,
    ConnectionSettings,
    SshSettings,
    TlsSettings,
)


def _prefer(value: str, fallback: str) -> str:
    if value != "":
        return value
    return fallback


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


def _valid_port(value: str) -> bool:
    if value == "":
        return True
    port = 0
    for character in value:
        if character < "0" or character > "9":
            return False
        port = port * 10 + ord(character) - ord("0")
        if port > 65535:
            return False
    return port > 0


def _tls_was_supplied(settings: TlsSettings) -> bool:
    root_certificate = str(settings.root_certificate)
    certificate = str(settings.certificate)
    private_key = str(settings.private_key)
    if settings.mode != "":
        return True
    if root_certificate != "" and root_certificate != ".":
        return True
    if certificate != "" and certificate != ".":
        return True
    return private_key != "" and private_key != "."


def _tls_validation_error(settings: TlsSettings) -> str:
    mode = settings.mode.casefold()
    if mode not in ("", "disable", "allow", "prefer", "require", "verify-ca", "verify-full"):
        return "invalid TLS mode: " + settings.mode
    certificate = str(settings.certificate)
    private_key = str(settings.private_key)
    certificate_present = certificate != "" and certificate != "."
    private_key_present = private_key != "" and private_key != "."
    if certificate_present and not private_key_present:
        return "TLS certificate requires a private key"
    if private_key_present and not certificate_present:
        return "TLS private key requires a certificate"
    return ""


def _ssh_validation_error(settings: SshSettings) -> str:
    if settings.host == "":
        return "SSH host is required"
    if settings.port == 0:
        return "SSH port must be greater than zero"
    if settings.user == "":
        return "SSH user is required"
    return ""


def _select_ssh(request_ssh: Option[SshSettings], profile_ssh: Option[SshSettings]) -> Option[SshSettings]:
    match request_ssh:
        case Some(value=request_settings):
            return Some(value=request_settings)
        case Nothing():
            return profile_ssh


def _ssh_option_validation_error(ssh: Option[SshSettings]) -> str:
    match ssh:
        case Some(value=settings):
            return _ssh_validation_error(settings)
        case Nothing():
            return ""


def resolve_connection_plan(request: ConnectionRequest, profile: Option[ConnectionProfile]) -> Result[ConnectionPlan, ConnectionError]:
    match profile:
        case Some(value=profile_value):
            has_profile = True
            profile_dsn = profile_value.dsn
            profile_inputs = profile_value.inputs
            profile_tls = profile_value.tls
            profile_ssh = profile_value.ssh
        case Nothing():
            has_profile = False
            profile_dsn = ""
            profile_inputs = ConnectionInputs(host="", port="", user="", password="", database="")
            profile_tls = request.tls
            profile_ssh = Nothing()

    host = ""
    port = ""
    user = ""
    password = ""
    database = ""
    selected_dsn = profile_dsn
    if profile_dsn != "" and request.dsn == "":
        valid, host, port, user, password, database = _parse_dsn_parts(profile_dsn)
        if not valid:
            return Err(error=ConnectionError_InvalidDsn(value=profile_dsn))
    host = _prefer(profile_inputs.host, host)
    port = _prefer(profile_inputs.port, port)
    user = _prefer(profile_inputs.user, user)
    password = _prefer(profile_inputs.password, password)
    database = _prefer(profile_inputs.database, database)

    if request.dsn != "":
        selected_dsn = request.dsn
        valid, dsn_host, dsn_port, dsn_user, dsn_password, dsn_database = _parse_dsn_parts(request.dsn)
        if not valid:
            return Err(error=ConnectionError_InvalidDsn(value=request.dsn))
        host = _prefer(dsn_host, host)
        port = _prefer(dsn_port, port)
        user = _prefer(dsn_user, user)
        password = _prefer(dsn_password, password)
        database = _prefer(dsn_database, database)

    host = _prefer(request.inputs.host, host)
    port = _prefer(request.inputs.port, port)
    user = _prefer(request.inputs.user, user)
    password = _prefer(request.inputs.password, password)
    database = _prefer(request.inputs.database, database)
    host = _prefer(host, request.environment.host)
    port = _prefer(port, request.environment.port)
    user = _prefer(user, request.environment.user)
    password = _prefer(password, request.environment.password)
    database = _prefer(database, request.environment.database)

    if database == "":
        return Err(error=ConnectionError_MissingDatabase())
    if not _valid_port(port):
        return Err(error=ConnectionError_InvalidPort(value=port))

    tls = request.tls
    if has_profile and not _tls_was_supplied(request.tls):
        tls = profile_tls
    tls_error = _tls_validation_error(tls)
    if tls_error != "":
        return Err(error=ConnectionError_TlsInvalid(message=tls_error))

    ssh = _select_ssh(request.ssh, profile_ssh)
    ssh_error = _ssh_option_validation_error(ssh)
    if ssh_error != "":
        return Err(error=ConnectionError_SshInvalid(message=ssh_error))

    settings = ConnectionSettings(host=host, port=port, user=user, password=password, database=database)
    return Ok(value=ConnectionPlan(settings=settings, dsn=selected_dsn, tls=tls, ssh=ssh))
