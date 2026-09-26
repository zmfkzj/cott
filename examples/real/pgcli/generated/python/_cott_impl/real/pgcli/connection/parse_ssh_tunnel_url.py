import urllib.parse

from cott_runtime import Nothing, Some
from real.pgcli.connection_types import SshTunnelTarget


def parse_ssh_tunnel_url(url: str) -> SshTunnelTarget:
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname
    port = parsed.port
    username = parsed.username
    password = parsed.password
    return SshTunnelTarget(
        host=hostname if hostname is not None else "",
        port=port if port is not None and port > 0 else 22,
        username=Some(value=username) if username is not None else Nothing(),
        password=Some(value=password) if password is not None else Nothing(),
    )
