import os
import pathlib
import shutil
import socket
import subprocess
import tempfile
import time
from typing import Any, Final

import psycopg
from psycopg.conninfo import conninfo_to_dict

from cott_runtime import Err, Ok, Result, Some, Unit, UNIT
from real.pgcli_types import ConnectionError, ConnectionError_ConnectionFailed, ConnectionPlan, SshSettings

_SSH: Final[str] = "ssh"
_TIMEOUT: Final[int] = 10
_CLEANUP_TIMEOUT: Final[int] = 5
_MSG_INVALID: Final[str] = "invalid connection configuration"
_MSG_SSH: Final[str] = "ssh tunnel failed"
_MSG_DB: Final[str] = "database connection failed"
_MSG_CLEANUP: Final[str] = "connection cleanup failed"
_TLS_MODES: Final[str] = "disable allow prefer require verify-ca verify-full"


def _valid_port(value: str) -> bool:
    if not value or not all("0" <= c <= "9" for c in value):
        return False
    return 1 <= int(value) <= 65535


def _has_control(value: str) -> bool:
    return any(ord(c) < 32 or ord(c) == 127 for c in value)


def _path_opt(value: pathlib.Path) -> str | None:
    text = str(value)
    return None if text == "." else text


def _resolve(plan: ConnectionPlan) -> dict[str, Any] | None:
    try:
        params: dict[str, Any] = dict(conninfo_to_dict(plan.dsn)) if plan.dsn else {}
    except Exception:
        return None
    s = plan.settings
    for key, value in (("host", s.host), ("port", s.port), ("user", s.user), ("password", s.password), ("dbname", s.database)):
        if value:
            params[key] = value
    dbname = params.get("dbname")
    if not isinstance(dbname, str) or not dbname:
        return None
    port = params.get("port")
    if port is None or port == "":
        params["port"] = "5432"
    elif not isinstance(port, str) or not _valid_port(port):
        return None
    tls = plan.tls
    mode = tls.mode or "prefer"
    if mode not in _TLS_MODES.split(" "):
        return None
    params["sslmode"] = mode
    root = _path_opt(tls.root_certificate)
    cert = _path_opt(tls.certificate)
    key = _path_opt(tls.private_key)
    if root == "" or cert == "" or key == "":
        return None
    if root is not None:
        params["sslrootcert"] = root
    if cert is not None:
        params["sslcert"] = cert
    if key is not None:
        params["sslkey"] = key
    if bool(params.get("sslcert")) != bool(params.get("sslkey")):
        return None
    params["connect_timeout"] = str(_TIMEOUT)
    return params


def _ssh_target_ok(ssh: SshSettings) -> bool:
    if not ssh.host or not ssh.user or ssh.port <= 0:
        return False
    if ssh.host.startswith("-") or ssh.user.startswith("-"):
        return False
    return not (_has_control(ssh.host) or _has_control(ssh.user))


def _db_host_ok(host: str) -> bool:
    if "," in host or host.startswith("/") or host.startswith("@") or host.startswith("-"):
        return False
    return not _has_control(host) and not any(c.isspace() for c in host)


def _run(args: list[str]) -> bool:
    try:
        done: subprocess.CompletedProcess[str] = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=_TIMEOUT, check=False, shell=False, text=True)
    except Exception:
        return False
    return done.returncode == 0


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
    return port


def _probe(params: dict[str, Any]) -> bool:
    conn: psycopg.Connection[Any] | None = None
    ok = False
    try:
        conn = psycopg.connect(autocommit=True, **params)
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            row = cur.fetchone()
        ok = row is not None and row[0] == 1
    except Exception:
        ok = False
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                ok = False
    return ok


def _stop_master(proc: subprocess.Popen[str], ctl: list[str], host: str) -> bool:
    clean = True
    if proc.poll() is None:
        _run(ctl + ["-O", "exit", "--", host])
        try:
            proc.wait(timeout=_CLEANUP_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=_CLEANUP_TIMEOUT)
            except subprocess.TimeoutExpired:
                proc.kill()
                try:
                    proc.wait(timeout=_CLEANUP_TIMEOUT)
                except subprocess.TimeoutExpired:
                    clean = False
    return clean


def _tunnel_probe(params: dict[str, Any], ssh: SshSettings) -> str | None:
    db_host = params.get("host") or "localhost"
    if not isinstance(db_host, str) or not _db_host_ok(db_host):
        return _MSG_INVALID
    if not _ssh_target_ok(ssh):
        return _MSG_INVALID
    db_port = str(params["port"])
    ssh_bin = shutil.which(_SSH)
    if ssh_bin is None:
        return _MSG_SSH
    key = _path_opt(ssh.private_key)
    try:
        tmp = tempfile.mkdtemp(prefix="pgcli-ssh-")
    except Exception:
        return _MSG_SSH
    result: str | None = None
    proc: subprocess.Popen[str] | None = None
    try:
        os.chmod(tmp, 0o700)
        sock_path = os.path.join(tmp, "cm")
        base = [ssh_bin, "-S", sock_path, "-p", str(ssh.port), "-l", ssh.user]
        opts = ["-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ExitOnForwardFailure=yes", "-o", "ConnectTimeout=10", "-o", "ControlPersist=no", "-o", "GatewayPorts=no", "-o", "PasswordAuthentication=no", "-o", "KbdInteractiveAuthentication=no"]
        identity = ["-i", key, "-o", "IdentitiesOnly=yes"] if key else []
        master = [ssh_bin, "-M", "-N", "-S", sock_path, "-p", str(ssh.port), "-l", ssh.user] + opts + identity + ["--", ssh.host]
        proc = subprocess.Popen(master, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False, text=True)
        ctl = base + ["-o", "BatchMode=yes"]
        deadline = time.monotonic() + _TIMEOUT
        ready = False
        while time.monotonic() < deadline and proc.poll() is None:
            if os.path.exists(sock_path) and _run(ctl + ["-O", "check", "--", ssh.host]):
                ready = True
                break
            time.sleep(0.1)
        if not ready:
            result = _MSG_SSH
        else:
            local_port = _free_port()
            fwd_host = f"[{db_host}]" if ":" in db_host else db_host
            spec = f"127.0.0.1:{local_port}:{fwd_host}:{db_port}"
            forwarded = _run(ctl + ["-O", "forward", "-L", spec, "--", ssh.host])
            if not forwarded or proc.poll() is not None or not _run(ctl + ["-O", "check", "--", ssh.host]):
                result = _MSG_SSH
            else:
                tunneled = dict(params)
                tunneled["host"] = db_host
                tunneled["hostaddr"] = "127.0.0.1"
                tunneled["port"] = str(local_port)
                if not _probe(tunneled):
                    result = _MSG_DB
        if not _stop_master(proc, ctl, ssh.host):
            result = result or _MSG_CLEANUP
        proc = None
    except Exception:
        result = result or _MSG_SSH
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=_CLEANUP_TIMEOUT)
            except Exception:
                proc.kill()
                try:
                    proc.wait(timeout=_CLEANUP_TIMEOUT)
                except Exception:
                    result = result or _MSG_CLEANUP
        try:
            shutil.rmtree(tmp)
        except Exception:
            result = result or _MSG_CLEANUP
    return result


def connect(plan: ConnectionPlan) -> Result[Unit, ConnectionError]:
    params = _resolve(plan)
    if params is None:
        return Err(error=ConnectionError_ConnectionFailed(message=_MSG_INVALID))
    ssh = plan.ssh
    if isinstance(ssh, Some):
        failure = _tunnel_probe(params, ssh.value)
        if failure is not None:
            return Err(error=ConnectionError_ConnectionFailed(message=failure))
        return Ok(value=UNIT)
    if not _probe(params):
        return Err(error=ConnectionError_ConnectionFailed(message=_MSG_DB))
    return Ok(value=UNIT)
