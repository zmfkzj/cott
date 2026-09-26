import subprocess
from typing import cast

from cott_runtime import UNIT, Unit
from real.harlequin.support_types import SshTunnel


def close_ssh_tunnel(tunnel: SshTunnel) -> Unit:
    if tunnel.reused:
        return UNIT
    handle = tunnel.process
    if handle.tag != "harlequin.ssh_process":
        raise TypeError(f"SshTunnel.process has unexpected tag {handle.tag!r}")
    raw = handle.unwrap()
    if not isinstance(raw, subprocess.Popen):
        raise TypeError("SshTunnel.process payload is not a subprocess.Popen")
    process = cast(subprocess.Popen[str], raw)
    if process.poll() is not None:
        return UNIT
    try:
        process.terminate()
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            return UNIT
    return UNIT
