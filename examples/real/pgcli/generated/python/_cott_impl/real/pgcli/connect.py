import os
import shutil
import socket
import subprocess
import tempfile
import time
from typing import Final

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from cott_runtime import Err, Ok, Result, Some
from real.pgcli_types import ConnectionError, ConnectionError_ConnectionFailed, ConnectionPlan, ConnectionReceipt, SshSettings, TlsMode, TlsMode_Allow, TlsMode_Disable, TlsMode_Prefer, TlsMode_Require, TlsMode_VerifyCa, TlsMode_VerifyFull

_TIMEOUT: Final[int] = 10
_CLEANUP_TIMEOUT: Final[int] = 5
_MSG_INVALID: Final[str] = "invalid connection configuration"
_MSG_SSH: Final[str] = "ssh tunnel failed"
_MSG_DB: Final[str] = "database connection failed"
_MSG_CLEANUP: Final[str] = "connection cleanup failed"


def _fail(message: str) -> Err[ConnectionError]:
    return Err(error=ConnectionError_ConnectionFailed(message=message))


def _has_control(value: str) -> bool:
    return any(ord(c) < 32 or ord(c) == 127 for c in value)


def _tls_mode(mode: TlsMode) -> str | None:
    if isinstance(mode, TlsMode_Disable):
        return "disable"
    if isinstance(mode, TlsMode_Allow):
        return "allow"
    if isinstance(mode, TlsMode_Prefer):
        return "prefer"
    if isinstance(mode, TlsMode_Require):
        return "require"
    if isinstance(mode, TlsMode_VerifyCa):
        return "verify-ca"
    if isinstance(mode, TlsMode_VerifyFull):
        return "verify-full"
    return None


def _ssl_rank(mode: str) -> int:
    order = ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
    return order.index(mode) if mode in order else -1


def _resolve(plan: ConnectionPlan) -> dict[str, str] | None:
    params: dict[str, str] = {}
    if plan.dsn:
        try:
            parsed = conninfo_to_dict(plan.dsn)
        except Exception:
            return None
        for key, value in parsed.items():
            if value is None:
                continue
            if isinstance(value, int):
                params[key] = str(value)
            else:
                params[key] = value
    s = plan.settings
    for key, value in (("host", s.host), ("port", s.port), ("user", s.user), ("password", s.password), ("dbname", s.database)):
        if value:
            params[key] = value
    tls = plan.tls
    mode = _tls_mode(tls.mode)
    existing = params.get("sslmode")
    if existing is not None and _ssl_rank(existing) < 0:
        return None
    if mode is not None:
        if existing is not None and _ssl_rank(existing) >= _ssl_rank("require") and _ssl_rank(mode) < _ssl_rank(existing):
            return None
        params["sslmode"] = mode
    root = tls.root_certificate
    if isinstance(root, Some):
        params["sslrootcert"] = os.fspath(root.value)
    client = tls.client
    if isinstance(client, Some):
        params["sslcert"] = os.fspath(client.value.certificate)
        params["sslkey"] = os.fspath(client.value.private_key)
    params["connect_timeout"] = str(_TIMEOUT)
    return params


def _probe(params: dict[str, str]) -> ConnectionReceipt | None:
    try:
        conninfo = make_conninfo("", **params)
    except Exception:
        return None
    receipt: ConnectionReceipt | None = None
    conn: psycopg.Connection[tuple[object, ...]] | None = None
    try:
        conn = psycopg.connect(conninfo, autocommit=True, connect_timeout=_TIMEOUT)
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_user, current_setting('server_version')")
            row = cur.fetchone()
        if row is not None and len(row) == 3:
            database, user, version = row[0], row[1], row[2]
            if isinstance(database, str) and isinstance(user, str) and isinstance(version, str):
                receipt = ConnectionReceipt(database=database, user=user, server_version=version)
    except Exception:
        receipt = None
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                receipt = None
    return receipt


def _run(args: list[str], timeout: float) -> bool:
    if timeout <= 0:
        return False
    try:
        done: subprocess.CompletedProcess[bytes] = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout, check=False, shell=False)
    except Exception:
        return False
    return done.returncode == 0


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
    return port


def _db_host_ok(host: str) -> bool:
    if not host or "," in host or host.startswith("/") or host.startswith("@") or host.startswith("-"):
        return False
    return not _has_control(host) and not any(c.isspace() for c in host)


def _port_ok(value: str) -> bool:
    if not value or not all("0" <= c <= "9" for c in value):
        return False
    return 1 <= int(value) <= 65535


def _wait(proc: subprocess.Popen[bytes]) -> bool:
    try:
        proc.wait(timeout=_CLEANUP_TIMEOUT)
    except subprocess.TimeoutExpired:
        return False
    return True


def _stop_master(proc: subprocess.Popen[bytes], ctl: list[str], host: str) -> bool:
    if proc.poll() is not None:
        return True
    _run(ctl + ["-O", "exit", "--", host], _CLEANUP_TIMEOUT)
    if _wait(proc):
        return True
    if proc.poll() is None:
        proc.terminate()
    if _wait(proc):
        return True
    if proc.poll() is None:
        proc.kill()
    proc.wait()
    return True


def _tunnel_probe(params: dict[str, str], hop: SshSettings) -> ConnectionReceipt | str:
    db_host = params.get("host") or "localhost"
    if not _db_host_ok(db_host):
        return _MSG_INVALID
    db_port = params.get("port") or "5432"
    if not _port_ok(db_port):
        return _MSG_INVALID
    if _has_control(hop.host) or _has_control(hop.user) or hop.user.startswith("-"):
        return _MSG_INVALID
    ssh_bin = shutil.which("ssh")
    if ssh_bin is None:
        return _MSG_SSH
    try:
        tmp = tempfile.mkdtemp(prefix="pgcli-ssh-")
    except Exception:
        return _MSG_SSH
    outcome: ConnectionReceipt | str = _MSG_SSH
    proc: subprocess.Popen[bytes] | None = None
    sock_path = os.path.join(tmp, "cm")
    ctl = [ssh_bin, "-S", sock_path, "-p", str(hop.port), "-l", hop.user, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ControlMaster=no"]
    try:
        os.chmod(tmp, 0o700)
        opts = ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ExitOnForwardFailure=yes", "-o", "ConnectTimeout=10", "-o", "ControlPersist=no", "-o", "GatewayPorts=no", "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no"]
        key = hop.private_key
        identity = ["-i", os.fspath(key.value), "-o", "IdentitiesOnly=yes"] if isinstance(key, Some) else []
        master = [ssh_bin, "-M", "-N", "-S", sock_path, "-p", str(hop.port), "-l", hop.user] + opts + identity + ["--", hop.host]
        proc = subprocess.Popen(master, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
        deadline = time.monotonic() + _TIMEOUT
        ready = False
        while time.monotonic() < deadline and proc.poll() is None:
            if os.path.exists(sock_path) and _run(ctl + ["-O", "check", "--", hop.host], deadline - time.monotonic()):
                ready = time.monotonic() < deadline
                break
            time.sleep(0.1)
        if ready:
            local_port = _free_port()
            fwd_host = f"[{db_host}]" if ":" in db_host else db_host
            spec = f"127.0.0.1:{local_port}:{fwd_host}:{db_port}"
            forwarded = _run(ctl + ["-O", "forward", "-L", spec, "--", hop.host], _TIMEOUT)
            if forwarded and proc.poll() is None and _run(ctl + ["-O", "check", "--", hop.host], _TIMEOUT):
                tunneled = dict(params)
                tunneled["host"] = db_host
                tunneled["hostaddr"] = "127.0.0.1"
                tunneled["port"] = str(local_port)
                receipt = _probe(tunneled)
                outcome = receipt if receipt is not None else _MSG_DB
    except Exception:
        outcome = _MSG_SSH
    finally:
        if proc is not None:
            try:
                if not _stop_master(proc, ctl, hop.host):
                    outcome = _MSG_CLEANUP
            except Exception:
                outcome = _MSG_CLEANUP
        try:
            shutil.rmtree(tmp)
        except Exception:
            outcome = _MSG_CLEANUP
    return outcome


def connect(plan: ConnectionPlan) -> Result[ConnectionReceipt, ConnectionError]:
    ssh = plan.ssh
    if isinstance(ssh, Some):
        hop = ssh.value
        if hop.host == "" or hop.host.startswith("-") or hop.user == "" or hop.port == 0:
            return _fail(_MSG_INVALID)
    params = _resolve(plan)
    if params is None:
        return _fail(_MSG_INVALID)
    if isinstance(ssh, Some):
        outcome = _tunnel_probe(params, ssh.value)
        if isinstance(outcome, str):
            return _fail(outcome)
        return Ok(value=outcome)
    receipt = _probe(params)
    if receipt is None:
        return _fail(_MSG_DB)
    return Ok(value=receipt)
