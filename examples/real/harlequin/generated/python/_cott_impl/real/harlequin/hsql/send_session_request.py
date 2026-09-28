import json
import os
import pathlib
import secrets
import socket
import struct
from typing import Final, cast

from cott_runtime import CottList, Err, FrozenMap, Ok, Option, Result, Some
from real.harlequin.hsql import session_socket_path
from real.harlequin.hsql_types import HSQL_PROTOCOL_VERSION, HsqlError, HsqlError_Connection, HsqlError_Interrupted, HsqlResponse

_HELLO: Final[int] = 1
_REQUEST: Final[int] = 2
_STDOUT: Final[int] = 3
_STDERR: Final[int] = 4
_EXIT: Final[int] = 5
_STATUS: Final[int] = 6
_CANCEL: Final[int] = 7
_MAX_FRAME_BYTES: Final[int] = 67108864


def _connection_error(message: str) -> Err[HsqlError]:
    return Err(error=HsqlError_Connection(message=message))


def _recv_exact(sock: socket.socket, size: int) -> bytes | None:
    received = bytearray()
    while len(received) < size:
        chunk = sock.recv(size - len(received))
        if not chunk:
            return None
        received.extend(chunk)
    return bytes(received)


def _read_frame(sock: socket.socket) -> tuple[int, bytes] | None:
    header = _recv_exact(sock, 5)
    if header is None:
        return None
    kind, length = cast(tuple[int, int], struct.unpack("!BI", header))
    if length > _MAX_FRAME_BYTES:
        return None
    payload = _recv_exact(sock, length)
    if payload is None:
        return None
    return kind, payload


def _send_frame(sock: socket.socket, kind: int, payload: bytes) -> None:
    if len(payload) > _MAX_FRAME_BYTES:
        raise ValueError("session frame exceeds 64 MiB")
    sock.sendall(struct.pack("!BI", kind, len(payload)))
    if payload:
        sock.sendall(payload)


def _cancel_request(path: pathlib.Path, request_id: str) -> None:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as other:
            other.connect(str(path))
            hello = _read_frame(other)
            if hello is not None and hello[0] == _HELLO:
                _send_frame(other, _CANCEL, request_id.encode("utf-8"))
    except OSError:
        return


def _exchange(sock: socket.socket, path: pathlib.Path, name: str, arguments: CottList[str], cwd: pathlib.Path, stdin_text: Option[str], environment: FrozenMap[str, str], stdout_tty: bool, stderr_tty: bool) -> Result[HsqlResponse, HsqlError]:
    closed = f"session '{name}' closed the connection"
    request_id: str | None = None
    try:
        hello = _read_frame(sock)
        if hello is None or hello[0] != _HELLO:
            return _connection_error(closed)
        version = hello[1].decode("utf-8")
        if version != HSQL_PROTOCOL_VERSION:
            return _connection_error(f"session '{name}' runs hsql {version}; restart it with this version")

        if "--session-status" in arguments:
            _send_frame(sock, _STATUS, b"")
            while True:
                frame = _read_frame(sock)
                if frame is None:
                    return _connection_error(closed)
                if frame[0] == _STATUS:
                    return Ok(value=HsqlResponse(stdout=frame[1] + b"\n", stderr="", status=0))

        request_id = secrets.token_hex(8)
        env: dict[str, str] = {}
        for key in ("NO_COLOR", "HARLEQUIN_CONFIG_PATH"):
            if key in environment:
                env[key] = environment[key]
        body: dict[str, object] = {
            "argv": list(arguments),
            "cwd": str(cwd),
            "env": env,
            "stdin": stdin_text.value if isinstance(stdin_text, Some) else None,
            "stdout_tty": stdout_tty,
            "stderr_tty": stderr_tty,
            "id": request_id,
        }
        _send_frame(sock, _REQUEST, json.dumps(body).encode("utf-8"))
        stdout = bytearray()
        stderr = bytearray()
        while True:
            frame = _read_frame(sock)
            if frame is None:
                return _connection_error(closed)
            kind, payload = frame
            if kind == _STDOUT:
                stdout.extend(payload)
            elif kind == _STDERR:
                stderr.extend(payload)
            elif kind == _EXIT:
                if len(payload) != 4:
                    return _connection_error(closed)
                status = cast(tuple[int], struct.unpack("!i", payload))[0]
                if status < 0:
                    return _connection_error(closed)
                return Ok(value=HsqlResponse(stdout=bytes(stdout), stderr=stderr.decode("utf-8"), status=status))
    except KeyboardInterrupt:
        if request_id is not None:
            _cancel_request(path, request_id)
        return Err(error=HsqlError_Interrupted())
    except (OSError, UnicodeDecodeError, ValueError):
        return _connection_error(closed)


def send_session_request(name: str, arguments: CottList[str], cwd: pathlib.Path, stdin_text: Option[str], environment: FrozenMap[str, str], stdout_tty: bool, stderr_tty: bool) -> Result[HsqlResponse, HsqlError]:
    path = session_socket_path(name, environment, os.getuid())
    missing = f"no session named '{name}' is running. Start one with `hsql --serve {name} ...`."
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            try:
                sock.connect(str(path))
            except OSError:
                return _connection_error(missing)
            return _exchange(sock, path, name, arguments, cwd, stdin_text, environment, stdout_tty, stderr_tty)
    except OSError:
        return _connection_error(missing)
    except KeyboardInterrupt:
        return Err(error=HsqlError_Interrupted())
