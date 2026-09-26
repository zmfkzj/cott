import json
import os
import pathlib
import socket
import stat
import struct
import sys
import threading
import time
from typing import Final, cast

import filelock
from cott_runtime import I64, CottList, FrozenMap, Nothing, Ok, Some

from real.harlequin.adapters import cancel_queries, close_connection, connect
from real.harlequin.adapters_types import Connection, ConnectionError_Failed, ConnectionError_InvalidOption, ConnectionRequest
from real.harlequin.hsql import execute_hsql_request, hsql_error_line, parse_hsql_arguments, session_socket_path, valid_session_name
from real.harlequin.hsql_types import HSQL_PROTOCOL_VERSION, HsqlArguments, HsqlContext, HsqlError_Connection, HsqlError_Timeout, HsqlError_Usage, HsqlMode_SessionReset, HsqlMode_SessionStatus, HsqlResponse
from real.harlequin.sqltext import redact_text

_HELLO: Final[int] = 1
_REQUEST: Final[int] = 2
_STDOUT: Final[int] = 3
_STDERR: Final[int] = 4
_EXIT: Final[int] = 5
_STATUS: Final[int] = 6
_CANCEL: Final[int] = 7
_MAX_PAYLOAD: Final[int] = 67108864
_CHUNK: Final[int] = 65536
_ADAPTERS: Final[str] = "adbc,bigquery,cassandra,chdb,databricks,duckdb,mysql,nebulagraph,odbc,postgres,sqlite,trino"


def _err(text: str) -> None:
    sys.stderr.write(text)
    sys.stderr.flush()


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
    if length > _MAX_PAYLOAD:
        return None
    body = _recv_exact(sock, length) if length else b""
    if body is None:
        return None
    return (kind, body)


def _send(sock: socket.socket, send_lock: threading.Lock, kind: int, payload: bytes) -> None:
    with send_lock:
        sock.sendall(struct.pack("!BI", kind, len(payload)) + payload)


def _open(request: ConnectionRequest) -> tuple[Connection | None, str]:
    opened = connect(request)
    if isinstance(opened, Ok):
        return (opened.value, "")
    error = opened.error
    if isinstance(error, ConnectionError_Failed) or isinstance(error, ConnectionError_InvalidOption):
        return (None, f"{error.title}\n{error.message}")
    return (None, f"The {error.adapter} adapter does not support read-only connections.")


def _status_json(name: str, context: HsqlContext, arguments: HsqlArguments, request: ConnectionRequest, conn_box: list[Connection], nums: dict[str, float]) -> bytes:
    now = time.monotonic()
    connection = conn_box[0] if conn_box else None
    state = "unavailable" if connection is None else ("busy" if nums["busy"] > 0 else "idle")
    mode: str | None = None
    if connection is not None:
        tm = connection.transaction_mode
        if isinstance(tm, Some):
            mode = tm.value.label
    expires: float | None = None
    if arguments.max_lifetime_seconds > 0:
        expires = round(max(0.0, arguments.max_lifetime_seconds - (now - nums["started"])), 3)
    body: dict[str, object] = {
        "session": name,
        "pid": os.getpid(),
        "version": HSQL_PROTOCOL_VERSION,
        "adapter": context.adapter_name,
        "connection": redact_text(connection.connection_id, context.secrets) if connection is not None else None,
        "connection_options": [setting.name for setting in request.settings],
        "uptime_s": round(now - nums["started"], 3),
        "requests": int(nums["requests"]),
        "state": state,
        "queued": int(nums["queued"]),
        "transaction_mode": mode,
        "ssh": None,
        "idle_timeout_s": arguments.idle_timeout_seconds,
        "expires_in_s": expires,
    }
    return json.dumps(body).encode("utf-8")


def _is_turn(line: list[int], nums: dict[str, float], ticket: int) -> bool:
    return nums["busy"] == 0 and len(line) > 0 and line[0] == ticket


def _leave_line(line: list[int], ticket: int) -> None:
    if ticket in line:
        line.remove(ticket)


def _take_turn(state_lock: threading.Condition, line: list[int], nums: dict[str, float], ticket: int, timeout: float | None) -> bool:
    with state_lock:
        nums["queued"] += 1
        acquired = state_lock.wait_for(lambda: _is_turn(line, nums, ticket), timeout=timeout)
        _leave_line(line, ticket)
        nums["queued"] -= 1
        if acquired:
            nums["busy"] = 1
        state_lock.notify_all()
        return acquired


def _run_request(name: str, payload: bytes, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, conn_box: list[Connection], nums: dict[str, float], ids: dict[str, str], line: list[int], state_lock: threading.Condition, ticket: int) -> HsqlResponse:
    try:
        raw = cast(object, json.loads(payload.decode("utf-8")))
    except (ValueError, UnicodeDecodeError) as error:
        return HsqlResponse(stdout=b"", stderr=hsql_error_line(HsqlError_Usage(message=f"malformed request: {error}")), status=2)
    if not isinstance(raw, dict):
        return HsqlResponse(stdout=b"", stderr=hsql_error_line(HsqlError_Usage(message="malformed request")), status=2)
    body = cast(dict[str, object], raw)
    argv_raw = body.get("argv")
    argv: list[str] = []
    if isinstance(argv_raw, list):
        for item in cast(list[object], argv_raw):
            if isinstance(item, str):
                argv.append(item)
    cwd_raw = body.get("cwd")
    cwd = pathlib.Path(cwd_raw) if isinstance(cwd_raw, str) else pathlib.Path.cwd()
    env_raw = body.get("env")
    env: dict[str, object] = cast(dict[str, object], env_raw) if isinstance(env_raw, dict) else {}
    stdin_raw = body.get("stdin")
    stdin_text: Some[str] | Nothing = Some(value=stdin_raw) if isinstance(stdin_raw, str) else Nothing()
    request_id = body.get("id")
    parsed = parse_hsql_arguments(CottList(values=argv), CottList(values=_ADAPTERS.split(",")), CottList(values=[]))
    if not isinstance(parsed, Ok):
        return HsqlResponse(stdout=b"", stderr=redact_text(hsql_error_line(parsed.error), context.secrets), status=2)
    args = parsed.value
    if isinstance(args.mode, HsqlMode_SessionStatus):
        with state_lock:
            text = _status_json(name, context, arguments, request, conn_box, nums)
        return HsqlResponse(stdout=text + b"\n", stderr="", status=0)
    queue = args.queue_timeout_seconds
    acquired = _take_turn(state_lock, line, nums, ticket, queue.value if isinstance(queue, Some) else None)
    if not acquired:
        waited = queue.value if isinstance(queue, Some) else 0.0
        message = f"waited {waited:g}s for the session's previous request and never reached the database (--queue-timeout)."
        return HsqlResponse(stdout=b"", stderr=hsql_error_line(HsqlError_Timeout(message=message)), status=4)
    try:
        with state_lock:
            ids["current"] = request_id if isinstance(request_id, str) else ""
        if isinstance(args.mode, HsqlMode_SessionReset):
            if conn_box:
                close_connection(conn_box[0])
                conn_box.clear()
            opened, failure = _open(request)
            if opened is None:
                return HsqlResponse(stdout=b"", stderr=redact_text(f"hsql: error: {failure}\n", context.secrets), status=3)
            conn_box.append(opened)
            return HsqlResponse(stdout=b"", stderr=f"note: session '{name}' reconnected.\n", status=0)
        if not conn_box:
            text = hsql_error_line(HsqlError_Connection(message=f"session '{name}' has no open connection; pass --session-reset to reconnect."))
            return HsqlResponse(stdout=b"", stderr=text, status=3)
        per_request = HsqlContext(
            profile=context.profile,
            adapter_name=context.adapter_name,
            query_log=context.query_log,
            stdout_tty=body.get("stdout_tty") is True,
            stderr_tty=body.get("stderr_tty") is True,
            no_color="NO_COLOR" in env,
            implements_cancel=context.implements_cancel,
            implements_catalog_search=context.implements_catalog_search,
            secrets=context.secrets,
        )
        return execute_hsql_request(conn_box[0], args, cwd, stdin_text, per_request)
    finally:
        with state_lock:
            nums["busy"] = 0
            ids["current"] = ""
            nums["last"] = time.monotonic()
            state_lock.notify_all()


def _peer(sock: socket.socket, name: str, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, conn_box: list[Connection], nums: dict[str, float], ids: dict[str, str], line: list[int], state_lock: threading.Condition) -> None:
    send_lock = threading.Lock()
    try:
        _send(sock, send_lock, _HELLO, HSQL_PROTOCOL_VERSION.encode("utf-8"))
        while True:
            frame = _read_frame(sock)
            if frame is None:
                return
            kind, payload = frame
            if kind == _STATUS:
                with state_lock:
                    text = _status_json(name, context, arguments, request, conn_box, nums)
                _send(sock, send_lock, _STATUS, text)
            elif kind == _CANCEL:
                wanted = payload.decode("utf-8", "replace").strip()
                with state_lock:
                    hit = wanted != "" and ids["current"] == wanted and nums["busy"] > 0
                if hit and conn_box:
                    cancel_queries(conn_box[0])
            elif kind == _REQUEST:
                with state_lock:
                    nums["requests"] += 1
                    number = int(nums["requests"])
                    nums["last"] = time.monotonic()
                    ticket = int(nums["ticket"])
                    nums["ticket"] += 1
                    line.append(ticket)
                started = time.monotonic()
                try:
                    response = _run_request(name, payload, request, context, arguments, conn_box, nums, ids, line, state_lock, ticket)
                finally:
                    with state_lock:
                        _leave_line(line, ticket)
                        state_lock.notify_all()
                data = response.stdout
                for offset in range(0, len(data), _CHUNK):
                    _send(sock, send_lock, _STDOUT, data[offset:offset + _CHUNK])
                if response.stderr:
                    _send(sock, send_lock, _STDERR, response.stderr.encode("utf-8"))
                _send(sock, send_lock, _EXIT, struct.pack("!i", response.status))
                elapsed = int((time.monotonic() - started) * 1000)
                _err(f"note: request {number}: exit {response.status} in {elapsed}ms\n")
    except OSError:
        return
    finally:
        sock.close()


def _spawn(peer: socket.socket, name: str, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, conn_box: list[Connection], nums: dict[str, float], ids: dict[str, str], line: list[int], state_lock: threading.Condition) -> None:
    worker = threading.Thread(target=lambda: _peer(peer, name, request, context, arguments, conn_box, nums, ids, line, state_lock), daemon=True)
    worker.start()


def _usage(message: str) -> I64:
    _err(hsql_error_line(HsqlError_Usage(message=message)))
    return 2


def _peer_uid(peer: socket.socket) -> int | None:
    size = struct.calcsize("3i")
    try:
        creds = peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, size)
    except OSError:
        return None
    if len(creds) != size:
        return None
    return cast(tuple[int, int, int], struct.unpack("3i", creds))[1]


def _check_dir(directory: pathlib.Path) -> str | None:
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = os.lstat(directory)
    except OSError as error:
        return f"could not create the session directory {directory}: {error.strerror or error}"
    if not stat.S_ISDIR(info.st_mode):
        return f"{directory} is not a directory."
    if info.st_uid != os.getuid():
        return f"{directory} is not owned by you."
    if info.st_mode & 0o077:
        return f"{directory} is accessible by other users; restrict it with chmod 700."
    return None


def _serve_loop(server: socket.socket, name: str, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, conn_box: list[Connection], nums: dict[str, float], ids: dict[str, str], line: list[int], state_lock: threading.Condition) -> None:
    uid = os.getuid()
    try:
        while True:
            now = time.monotonic()
            with state_lock:
                idle = nums["busy"] == 0 and nums["queued"] == 0
                last = nums["last"]
            if arguments.max_lifetime_seconds > 0 and now - nums["started"] >= arguments.max_lifetime_seconds and idle:
                return
            if arguments.idle_timeout_seconds > 0 and idle and now - last >= arguments.idle_timeout_seconds:
                return
            try:
                peer, _ = server.accept()
            except TimeoutError:
                continue
            peer_uid = _peer_uid(peer)
            if peer_uid is None:
                _err("note: refused a connection whose owner could not be verified.\n")
                peer.close()
                continue
            if peer_uid != uid:
                _err(f"note: refused a connection from uid {peer_uid}, which is not yours.\n")
                peer.close()
                continue
            peer.settimeout(None)
            _spawn(peer, name, request, context, arguments, conn_box, nums, ids, line, state_lock)
    except KeyboardInterrupt:
        return


def serve_hsql_session(name: str, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, environment: FrozenMap[str, str]) -> I64:
    if not valid_session_name(name):
        return _usage(f"invalid session name '{name}': use 1 to 64 letters, digits, _ or -")
    if not sys.platform.startswith("linux"):
        return _usage(f"hsql --serve needs to verify which user connects to the session socket, which {sys.platform} does not support.")
    socket_path = pathlib.Path(session_socket_path(name, environment, os.getuid()))
    problem = _check_dir(socket_path.parent)
    if problem is not None:
        return _usage(problem)
    lock = filelock.FileLock(str(socket_path.parent / f"{name}.lock"), timeout=0)
    try:
        lock.acquire()
    except filelock.Timeout:
        return _usage(f"session '{name}' is already running")
    try:
        if socket_path.exists() or socket_path.is_symlink():
            socket_path.unlink()
        opened, failure = _open(request)
        if opened is None:
            _err(redact_text(f"hsql: error: {failure}\n", context.secrets))
            return 3
        conn_box: list[Connection] = [opened]
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        nums: dict[str, float] = {"started": time.monotonic(), "last": time.monotonic(), "requests": 0.0, "queued": 0.0, "busy": 0.0, "ticket": 0.0}
        try:
            server.bind(str(socket_path))
            os.chmod(socket_path, 0o600)
            server.listen(16)
            server.settimeout(0.5)
            _err(f"note: session '{name}' is ready ({context.adapter_name}). Send it queries with `hsql --session {name} -c ...`, or set HSQL_SESSION={name}. Ctrl-C stops it.\n")
            _serve_loop(server, name, request, context, arguments, conn_box, nums, {"current": ""}, [], threading.Condition())
        finally:
            server.close()
            if conn_box:
                close_connection(conn_box[0])
            if socket_path.exists() or socket_path.is_symlink():
                socket_path.unlink(missing_ok=True)
        _err(f"note: session '{name}' stopped after {int(nums['requests'])} request(s).\n")
        return 0
    finally:
        lock.release()
