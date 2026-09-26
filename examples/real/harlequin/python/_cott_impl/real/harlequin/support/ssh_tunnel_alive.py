import socket
import subprocess
from typing import cast

from real.harlequin.support_types import SshTunnel


def ssh_tunnel_alive(tunnel: SshTunnel) -> bool:
    if tunnel.reused:
        for port in tunnel.local_ports:
            try:
                connection = socket.create_connection(("127.0.0.1", port), timeout=0.5)
                connection.close()
            except OSError:
                return False
        return True
    if tunnel.process.tag != "harlequin.ssh_process":
        raise ValueError("Expected a harlequin.ssh_process handle")
    process = cast(subprocess.Popen[str], tunnel.process.unwrap())
    return process.poll() is None
