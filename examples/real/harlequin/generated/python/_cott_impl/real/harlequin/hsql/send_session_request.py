import json
import os
import pathlib
import secrets
import socket
import struct
from typing import Final, cast

from cott_runtime import CottList, Err, FrozenMap, Nothing, Ok, Result, Some

from real.harlequin.hsql import session_socket_path
from real.harlequin.hsql_types import HSQL_PROTOCOL_VERSION, HsqlError, HsqlError_Connection, HsqlError_Interrupted, HsqlResponse

_HELLO: Final[int] = 1
_REQUEST: Final[int] = 2
_STDOUT: Final[int] = 3
_STDERR: Final[int] = 4
_EXIT: Final[int] = 5
_STATUS: Final[int] = 6
_CANCEL: Final[int] = 7


def _connection_error(message: str) -> Result[HsqlResponse, HsqlError]:
    return Err(error=HsqlError_Connection(message=message))


def _recv_exact(sock: socket.socket, size: int) -> bytes | None:
    buf = bytearray()
    while len(buf) < size:
        part = sock.recv(size - len(buf))
        if not part:
            return None
        buf.extend(part)
    return bytes(buf)


def _read_frame(sock: socket.socket) -> tuple[int, bytes] | None:
    head = _recv_exact(sock, 5)
    if head is None:
        return None
    kind, length = cast(tuple[int, int], struct.unpack("!BI", head))
    body = _recv_exact(sock, length) if length else b""
    if body is None:
        return None
    return (kind, body)


def _send(sock: socket.socket, kind: int, payload: bytes) -> None:
    sock.sendall(struct.pack("!BI", kind, len(payload)) + payload)


def _check_hello(sock: socket.socket, name: str) -> Result[HsqlResponse, HsqlError] | None:
    hello = _read_frame(sock)
    if hello is None or hello[0] != _HELLO:
        return _connection_error(f"session '{name}' closed the connection")
    version = hello[1].decode("utf-8", "replace")
    if version != HSQL_PROTOCOL_VERSION:
        return _connection_error(f"session '{name}' runs hsql {version}; restart it with this version")
    return None


def _cancel(path: str, request_id: str) -> None:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as other:
            other.connect(path)
            _read_frame(other)
            _send(other, _CANCEL, request_id.encode("utf-8"))
    except OSError:
        return


def _exchange(sock: socket.socket, path: str, name: str, argv: list[str], cwd: pathlib.Path, stdin_text: Some[str] | Nothing, environment: FrozenMap[str, str], stdout_tty: bool, stderr_tty: bool) -> Result[HsqlResponse, HsqlError]:
    bad = _check_hello(sock, name)
    if bad is not None:
        return bad
    closed = f"session '{name}' closed the connection"
    if "--session-status" in argv:
        _send(sock, _STATUS, b"")
        while True:
            frame = _read_frame(sock)
            if frame is None:
                return _connection_error(closed)
            if frame[0] == _STATUS:
                return Ok(value=HsqlResponse(stdout=frame[1] + b"\n", stderr="", status=0))
    env: dict[str, str] = {}
    for key in ("NO_COLOR", "HARLEQUIN_CONFIG_PATH"):
        if key in environment:
            env[key] = environment[key]
    request_id = secrets.token_hex(8)
    body: dict[str, object] = {
        "argv": argv,
        "cwd": str(cwd),
        "env": env,
        "stdin": stdin_text.value if isinstance(stdin_text, Some) else None,
        "stdout_tty": stdout_tty,
        "stderr_tty": stderr_tty,
        "id": request_id,
    }
    out = bytearray()
    err: list[str] = []
    try:
        _send(sock, _REQUEST, json.dumps(body).encode("utf-8"))
        while True:
            frame = _read_frame(sock)
            if frame is None:
                return _connection_error(closed)
            kind, payload = frame
            if kind == _STDOUT:
                out.extend(payload)
            elif kind == _STDERR:
                err.append(payload.decode("utf-8", "replace"))
            elif kind == _EXIT:
                if len(payload) != 4:
                    return _connection_error(closed)
                status = cast(tuple[int], struct.unpack("!i", payload))[0]
                return Ok(value=HsqlResponse(stdout=bytes(out), stderr="".join(err), status=status))
    except KeyboardInterrupt:
        _cancel(path, request_id)
        return Err(error=HsqlError_Interrupted())


def send_session_request(name: str, arguments: CottList[str], cwd: pathlib.Path, stdin_text: Some[str] | Nothing, environment: FrozenMap[str, str], stdout_tty: bool, stderr_tty: bool) -> Result[HsqlResponse, HsqlError]:
    path = str(session_socket_path(name, environment, os.getuid()))
    argv = [item for item in arguments]
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        try:
            sock.connect(path)
        except OSError:
            return _connection_error(f"no session named '{name}' is running. Start one with `hsql --serve {name} ...`.")
        try:
            return _exchange(sock, path, name, argv, cwd, stdin_text, environment, stdout_tty, stderr_tty)
        except OSError:
            return _connection_error(f"session '{name}' closed the connection")
    finally:
        sock.close()
