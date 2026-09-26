import re

from cott_runtime import CottList, Nothing, Option, Some

from real.pgcli.config_types import ConfigEntry


def find_ssh_tunnel_url(explicit: Option[str], dsn_alias: Option[str], host: str, dsn_tunnels: CottList[ConfigEntry], host_tunnels: CottList[ConfigEntry]) -> Option[str]:
    if isinstance(explicit, Some):
        url = explicit.value
    else:
        url = None
        if isinstance(dsn_alias, Some):
            for entry in dsn_tunnels:
                if re.search(entry.name, dsn_alias.value):
                    url = entry.value
                    break
        else:
            for entry in host_tunnels:
                if re.search(entry.name, host):
                    url = entry.value
                    break
    if url is None:
        return Nothing()
    if "://" not in url:
        url = "ssh://" + url
    return Some(value=url)
