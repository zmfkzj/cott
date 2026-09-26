import socket
import subprocess
import time
from typing import Final

from cott_runtime import CottList, Err, Ok, Opaque, Result, U64

from real.harlequin.cli_types import SshSettings
from real.harlequin.support import ssh_command
from real.harlequin.support_types import SshError, SshError_Failed, SshTunnel

_FAILED_PREFIX: Final[str] = "Harlequin could not open the SSH tunnel. "
_STDERR_LIMIT: Final[int] = 8192


def _failed(message: str) -> Result[SshTunnel, SshError]:
    return Err(error=SshError_Failed(message=_FAILED_PREFIX + message))


def _parse_port(spec: str) -> int | None:
    tail = spec.rsplit(":", 1)[-1]
    if tail.isdigit():
        return int(tail)
    return None


def _port_bound(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return True
    return False


def _port_accepts(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def _stop(process: subprocess.Popen[str]) -> str:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    stream = process.stderr
    if stream is None:
        return ""
    try:
        return stream.read(_STDERR_LIMIT).strip()
    except (OSError, ValueError):
        return ""
    finally:
        stream.close()


def open_ssh_tunnel(settings: SshSettings) -> Result[SshTunnel, SshError]:
    built = ssh_command(settings)
    if isinstance(built, Err):
        return Err(error=built.error)
    command = list(built.value)

    probe_command = ["ssh", "-G"]
    for forward in settings.forwards:
        probe_command.extend(["-L", forward])
    probe_command.append(settings.host)
    try:
        resolved: subprocess.CompletedProcess[str] = subprocess.run(probe_command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=10.0, check=False)
    except subprocess.TimeoutExpired:
        return _failed("Timed out resolving the ssh configuration.")
    except OSError as error:
        return _failed(str(error))
    if resolved.returncode != 0:
        return _failed(resolved.stderr.strip()[:_STDERR_LIMIT] or "ssh -G failed.")

    ports: list[int] = []
    interval = 0
    for line in resolved.stdout.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        key = parts[0].lower()
        if key == "localforward":
            port = _parse_port(parts[1])
            if port is not None and port not in ports:
                ports.append(port)
        elif key == "serveraliveinterval" and parts[1].isdigit():
            interval = int(parts[1])

    warnings: list[str] = []
    reused = False
    for port in ports:
        if _port_bound(port):
            if not settings.allow_reuse:
                return _failed(f"Local port {port} is already in use. Pass --ssh-allow-reuse to connect through it.")
            warnings.append(f"Port {port} is already in use; connecting through the listener that has it.")
            reused = True

    if interval == 0:
        command = command[:1] + ["-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=3"] + command[1:]
    try:
        process: subprocess.Popen[str] = subprocess.Popen(command, stdin=subprocess.DEVNULL if settings.batch_mode else None, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    except OSError as error:
        return _failed(str(error))

    deadline = time.monotonic() + (settings.timeout_seconds if ports else 1.0)
    ready = False
    while True:
        if process.poll() is not None:
            break
        if ports and all(_port_accepts(port) for port in ports):
            ready = True
            break
        if time.monotonic() >= deadline:
            ready = not ports and process.poll() is None
            break
        time.sleep(0.05)

    if not ready:
        detail = _stop(process)
        return _failed(detail or "Timed out waiting for the forwards.")

    local_ports: list[U64] = list(ports)
    return Ok(value=SshTunnel(host=settings.host, local_ports=CottList(values=local_ports), reused=reused, warnings=CottList(values=warnings), process=Opaque(tag="harlequin.ssh_process", value=process)))
