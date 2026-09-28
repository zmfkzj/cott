import dataclasses
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
from cott_runtime import CottList, FrozenMap, I64, Nothing, Ok, Some
from real.harlequin.adapters import cancel_queries, close_connection, connect
from real.harlequin.adapters_types import AdapterOption, Connection, ConnectionError_Failed, ConnectionError_InvalidOption, ConnectionRequest, OptionKind, OptionKind_FilePath, OptionKind_Flag, OptionKind_Repeated, OptionKind_Text, SettingValue_Flag, SettingValue_Text
from real.harlequin.hsql import execute_hsql_request, hsql_error_line, parse_hsql_arguments, session_socket_path, valid_session_name
from real.harlequin.hsql_types import HSQL_PROTOCOL_VERSION, HsqlArguments, HsqlContext, HsqlError, HsqlError_Connection, HsqlError_Crash, HsqlError_Timeout, HsqlError_Usage, HsqlMode_Catalog, HsqlMode_CatalogSearch, HsqlMode_Execute, HsqlMode_SessionReset, HsqlMode_SessionStatus, HsqlResponse
from real.harlequin.sqltext import redact_connection_string, redact_text

_HELLO: Final[int] = 1
_REQUEST: Final[int] = 2
_STDOUT: Final[int] = 3
_STDERR: Final[int] = 4
_EXIT: Final[int] = 5
_STATUS: Final[int] = 6
_CANCEL: Final[int] = 7
_MAX_FRAME: Final[int] = 67108864
_CHUNK: Final[int] = 65536
_ADAPTERS: Final[str] = "adbc,bigquery,cassandra,chdb,databricks,duckdb,mysql,nebulagraph,odbc,postgres,sqlite,trino"


def _stderr(text: str) -> None:
    sys.stderr.write(text)
    sys.stderr.flush()


def _redacted(text: str, context: HsqlContext) -> str:
    return redact_text(redact_connection_string(text), context.secrets)


def _usage(message: str) -> I64:
    _stderr(hsql_error_line(HsqlError_Usage(message=message)))
    return 2


def _error_response(failure: HsqlError, status: I64) -> HsqlResponse:
    return HsqlResponse(stdout=b"", stderr=hsql_error_line(failure), status=status)


def _check_directory(directory: pathlib.Path) -> str | None:
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = os.lstat(directory)
    except OSError as error:
        return f"could not create the session directory {directory}: {error}"
    if not stat.S_ISDIR(info.st_mode):
        return f"{directory} is not a real directory."
    if info.st_uid != os.getuid():
        return f"{directory} is not owned by you."
    if info.st_mode & 0o077 or info.st_mode & 0o700 != 0o700:
        return f"{directory} must have permissions 0700."
    return None


def _remove_socket(path: pathlib.Path) -> str | None:
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError as error:
        return f"could not inspect session socket {path}: {error}"
    if not stat.S_ISSOCK(info.st_mode):
        return f"{path} exists but is not a session socket."
    try:
        path.unlink()
    except OSError as error:
        return f"could not remove session socket {path}: {error}"
    return None


def _open(request: ConnectionRequest) -> tuple[Connection | None, str]:
    opened = connect(request)
    if isinstance(opened, Ok):
        return opened.value, ""
    failure = opened.error
    if isinstance(failure, (ConnectionError_Failed, ConnectionError_InvalidOption)):
        return None, f"{failure.title}\n{failure.message}"
    return None, f"Harlequin could not initialize the selected adapter.\nThe {failure.adapter} adapter does not support read-only connections."


def _options(request: ConnectionRequest, adapter_name: str) -> CottList[AdapterOption]:
    known: dict[str, str] = {
        "duckdb": "md_token md_saas allow_unsigned_extensions custom_extension_repo force_install_extensions extension no_init init_path",
        "sqlite": "mode lock_timeout detect_types isolation_level cached_statements extension no_init init_path",
        "postgres": "host port user password dbname sslmode sslrootcert sslcert sslkey connect_timeout application_name options",
        "mysql": "host port unix_socket database user password password1 password2 password3 connection_timeout ssl_ca ssl_cert ssl_key ssl_disabled openid_token_file enable_cleartext_plugin",
        "odbc": "", "bigquery": "project location",
        "trino": "host port user catalog schema require_auth password sslcert",
        "databricks": "server_hostname http_path access_token username password auth_type client_id client_secret no_init init_path skip_legacy_indexing",
        "adbc": "driver_type driver_path db_kwargs_str",
        "cassandra": "host port protocol_version user password keyspace consistency_level",
        "nebulagraph": "host port user password",
        "chdb": "uri path show_system catalog_search_limit",
    }
    flags = {"md_saas", "allow_unsigned_extensions", "force_install_extensions", "no_init", "ssl_disabled", "enable_cleartext_plugin", "skip_legacy_indexing", "show_system"}
    repeated = {"extension"}
    paths = {"init_path", "ssl_ca", "ssl_cert", "ssl_key", "sslcert", "sslrootcert", "sslkey", "openid_token_file", "driver_path"}
    reserved = {"adapter", "command", "file", "output", "format", "profile", "config_path", "read_only", "timeout", "path", "limit", "ssh_host", "ssh_forward", "ssh_batch_mode", "ssh_allow_reuse", "ssh_timeout", "catalog", "catalog_search", "history", "history_search", "session", "serve", "session_reset", "session_status", "queue_timeout", "idle_timeout", "max_lifetime", "stats", "color", "result", "display_rows", "on_error", "no_write_history", "no_header", "no_footer", "no_align", "tuples_only", "null_string"}
    names = known.get(adapter_name.lower(), "").split()
    for setting in request.settings:
        key = setting.name.replace("-", "_")
        if key not in names:
            names.append(key)
    options: list[AdapterOption] = []
    for key in names:
        if key in reserved:
            continue
        inferred: OptionKind | None = None
        for setting in request.settings:
            if setting.name.replace("-", "_") == key:
                value = setting.value
                if isinstance(value, SettingValue_Flag):
                    inferred = OptionKind_Flag()
                elif isinstance(value, SettingValue_Text):
                    inferred = OptionKind_Text()
                else:
                    inferred = OptionKind_Repeated()
                break
        kind: OptionKind
        if key in flags:
            kind = OptionKind_Flag()
        elif key in repeated:
            kind = OptionKind_Repeated()
        elif key in paths:
            kind = OptionKind_FilePath()
        elif inferred is not None:
            kind = inferred
        else:
            kind = OptionKind_Text()
        shorts = ["-e"] if key == "extension" and adapter_name.lower() in ("duckdb", "sqlite") else (["-i", "-init"] if key == "init_path" and adapter_name.lower() in ("duckdb", "sqlite") else [])
        options.append(AdapterOption(name=key.replace("_", "-"), short_decls=CottList(values=shorts), kind=kind, label=key.replace("_", "-"), description="", default=Nothing(), secret=any(part in key for part in ("password", "secret", "token", "ssl_key", "sslkey"))))
    return CottList(values=options)


def _status_json(name: str, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, cells: dict[str, object]) -> bytes:
    connections = cast(list[Connection], cells["connections"])
    counts = cast(dict[str, int], cells["counts"])
    times = cast(dict[str, float], cells["times"])
    now = time.monotonic()
    connection = connections[0] if connections else None
    transaction_mode: str | None = None
    if connection is not None and connection.session.tag == "harlequin.session":
        raw = connection.session.unwrap()
        if isinstance(raw, dict):
            payload = cast(dict[str, object], raw)
            if set(payload) == {"adapter", "driver", "request", "cleanup", "lock", "closed", "transaction_mode", "modes", "active"}:
                label = payload["transaction_mode"]
                if isinstance(label, str):
                    transaction_mode = label
    expires: float | None = None
    if arguments.max_lifetime_seconds > 0:
        expires = round(max(0.0, arguments.max_lifetime_seconds - (now - times["started"])), 3)
    details: dict[str, object] = {
        "session": name,
        "pid": os.getpid(),
        "version": HSQL_PROTOCOL_VERSION,
        "adapter": context.adapter_name,
        "connection": _redacted(connection.connection_id, context) if connection is not None else None,
        "connection_options": [setting.name for setting in request.settings],
        "uptime_s": round(now - times["started"], 3),
        "requests": counts["requests"],
        "state": "unavailable" if connection is None else ("busy" if counts["busy"] else "idle"),
        "queued": counts["queued"],
        "transaction_mode": transaction_mode,
        "ssh": None,
        "idle_timeout_s": arguments.idle_timeout_seconds,
        "expires_in_s": expires,
    }
    return json.dumps(details, separators=(",", ":")).encode("utf-8")


def _receive(peer: socket.socket, count: int) -> bytes | None:
    data = bytearray()
    while len(data) < count:
        piece = peer.recv(count - len(data))
        if not piece:
            return None
        data.extend(piece)
    return bytes(data)


def _read_frame(peer: socket.socket) -> tuple[int, bytes] | None:
    header = _receive(peer, 5)
    if header is None:
        return None
    kind, size = cast(tuple[int, int], struct.unpack("!BI", header))
    if size > _MAX_FRAME:
        return None
    body = _receive(peer, size)
    if body is None:
        return None
    return kind, body


def _send(peer: socket.socket, send_lock: threading.Lock, kind: int, body: bytes) -> None:
    if len(body) > _MAX_FRAME:
        raise OSError("session frame exceeds 64 MiB")
    with send_lock:
        peer.sendall(struct.pack("!BI", kind, len(body)))
        if body:
            peer.sendall(body)


def _send_stderr(peer: socket.socket, send_lock: threading.Lock, text: str) -> None:
    encoded = text.encode("utf-8")
    start = 0
    while start < len(encoded):
        end = min(start + _CHUNK, len(encoded))
        while end < len(encoded) and encoded[end] & 0xC0 == 0x80:
            end -= 1
        _send(peer, send_lock, _STDERR, encoded[start:end])
        start = end


def _request_body(payload: bytes) -> tuple[list[str], pathlib.Path, Some[str] | Nothing, bool, bool, bool, str, str | None] | None:
    try:
        raw: object = cast(object, json.loads(payload.decode("utf-8")))
    except (ValueError, UnicodeDecodeError):
        return None
    if not isinstance(raw, dict):
        return None
    body = cast(dict[str, object], raw)
    if not all(key in body for key in ("argv", "cwd", "env", "stdin", "stdout_tty", "stderr_tty", "id")):
        return None
    argv_raw = body["argv"]
    cwd_raw = body["cwd"]
    env_raw = body["env"]
    stdin_raw = body["stdin"]
    stdout_tty = body["stdout_tty"]
    stderr_tty = body["stderr_tty"]
    request_id = body["id"]
    if not isinstance(argv_raw, list) or not isinstance(cwd_raw, str) or not isinstance(env_raw, dict) or not isinstance(stdout_tty, bool) or not isinstance(stderr_tty, bool) or not isinstance(request_id, str):
        return None
    if stdin_raw is not None and not isinstance(stdin_raw, str):
        return None
    if not request_id or any(ch not in "0123456789abcdefABCDEF" for ch in request_id):
        return None
    argv: list[str] = []
    for item in cast(list[object], argv_raw):
        if not isinstance(item, str):
            return None
        argv.append(item)
    env = cast(dict[str, object], env_raw)
    if any(key not in ("NO_COLOR", "HARLEQUIN_CONFIG_PATH") or not isinstance(value, str) for key, value in env.items()):
        return None
    config = env.get("HARLEQUIN_CONFIG_PATH")
    config_path = config if isinstance(config, str) and config else None
    stdin_text: Some[str] | Nothing = Some(value=stdin_raw) if isinstance(stdin_raw, str) else Nothing()
    return argv, pathlib.Path(cwd_raw), stdin_text, stdout_tty, stderr_tty, "NO_COLOR" in env, request_id.lower(), config_path


def _ready_to_run(cells: dict[str, object], ticket: int) -> bool:
    counts = cast(dict[str, int], cells["counts"])
    waiting = cast(list[int], cells["line"])
    return cells["stopping"] is True or (counts["busy"] == 0 and counts["cancelling"] == 0 and bool(waiting) and waiting[0] == ticket)


def _take_turn(cells: dict[str, object], ticket: int, timeout: float | None, received: float) -> str:
    condition = cast(threading.Condition, cells["condition"])
    counts = cast(dict[str, int], cells["counts"])
    waiting = cast(list[int], cells["line"])
    with condition:
        remaining = None if timeout is None else max(0.0, timeout - (time.monotonic() - received))
        signaled = condition.wait_for(lambda: _ready_to_run(cells, ticket), timeout=remaining)
        at_front = bool(waiting) and waiting[0] == ticket
        if ticket in waiting:
            waiting.remove(ticket)
            counts["queued"] -= 1
        if cells["stopping"] is True:
            result = "stopping"
        elif signaled and at_front and counts["busy"] == 0 and counts["cancelling"] == 0 and (timeout is None or time.monotonic() - received <= timeout):
            counts["busy"] = 1
            result = "ready"
        else:
            result = "timeout"
        condition.notify_all()
    return result


def _run_request(name: str, payload: bytes, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, cells: dict[str, object], ticket: int, received: float) -> HsqlResponse:
    decoded = _request_body(payload)
    if decoded is None:
        return _error_response(HsqlError_Usage(message="malformed request"), 2)
    argv, cwd, stdin_text, stdout_tty, stderr_tty, no_color, request_id, config_path = decoded
    adapter_names = cast(CottList[str], cells["adapter_names"])
    adapter_options = cast(CottList[AdapterOption], cells["adapter_options"])
    parsed = parse_hsql_arguments(CottList(values=argv), adapter_names, adapter_options)
    if not isinstance(parsed, Ok):
        return _error_response(parsed.error, 2)
    args = parsed.value
    if config_path is not None and not isinstance(args.config_path, Some):
        args = dataclasses.replace(args, config_path=Some(value=config_path))
    condition = cast(threading.Condition, cells["condition"])
    connections = cast(list[Connection], cells["connections"])
    counts = cast(dict[str, int], cells["counts"])
    if isinstance(args.mode, HsqlMode_SessionStatus):
        with condition:
            waiting = cast(list[int], cells["line"])
            if ticket in waiting:
                waiting.remove(ticket)
                counts["queued"] -= 1
                condition.notify_all()
            status = _status_json(name, request, context, arguments, cells)
        return HsqlResponse(stdout=status + b"\n", stderr="", status=0)
    if not isinstance(args.mode, (HsqlMode_Execute, HsqlMode_Catalog, HsqlMode_CatalogSearch, HsqlMode_SessionReset)):
        return _error_response(HsqlError_Usage(message="this mode cannot run as a session request."), 2)
    queue_timeout = args.queue_timeout_seconds
    timeout = queue_timeout.value if isinstance(queue_timeout, Some) else None
    turn = _take_turn(cells, ticket, timeout, received)
    if turn == "timeout":
        waited = timeout if timeout is not None else 0.0
        return _error_response(HsqlError_Timeout(message=f"waited {waited:g}s for the session's previous request and never reached the database (--queue-timeout)."), 4)
    if turn == "stopping":
        return _error_response(HsqlError_Connection(message=f"session '{name}' is stopping."), 3)
    times = cast(dict[str, float], cells["times"])
    try:
        with condition:
            cells["current"] = "" if isinstance(args.mode, HsqlMode_SessionReset) else request_id
            connection = connections[0] if connections else None
        if isinstance(args.mode, HsqlMode_SessionReset):
            if connection is not None:
                with condition:
                    connections.clear()
                closed = close_connection(connection)
                if not isinstance(closed, Ok):
                    failure = closed.error
                    return _error_response(HsqlError_Connection(message=f"{failure.title}\n{failure.message}"), 3)
            reopened, failure_text = _open(request)
            if reopened is None:
                return _error_response(HsqlError_Connection(message=failure_text), 3)
            with condition:
                connections.append(reopened)
            return HsqlResponse(stdout=b"", stderr=f"note: session '{name}' reconnected.\n", status=0)
        if connection is None:
            return _error_response(HsqlError_Connection(message=f"session '{name}' has no open connection; pass --session-reset to reconnect."), 3)
        per_request = HsqlContext(profile=context.profile, adapter_name=context.adapter_name, query_log=context.query_log, stdout_tty=stdout_tty, stderr_tty=stderr_tty, no_color=no_color, implements_cancel=context.implements_cancel, implements_catalog_search=context.implements_catalog_search, secrets=context.secrets)
        return execute_hsql_request(connection, args, cwd, stdin_text, per_request)
    finally:
        with condition:
            counts["busy"] = 0
            cells["current"] = ""
            times["last"] = time.monotonic()
            condition.notify_all()


def _peer_first(peer_line: list[int], ticket: int) -> bool:
    return bool(peer_line) and peer_line[0] == ticket


def _deliver(peer: socket.socket, send_lock: threading.Lock, response: HsqlResponse, context: HsqlContext) -> None:
    try:
        for start in range(0, len(response.stdout), _CHUNK):
            _send(peer, send_lock, _STDOUT, response.stdout[start:start + _CHUNK])
        _send_stderr(peer, send_lock, _redacted(response.stderr, context))
        _send(peer, send_lock, _EXIT, struct.pack("!i", response.status))
    except OSError:
        return


def _request_worker(peer: socket.socket, send_lock: threading.Lock, peer_condition: threading.Condition, peer_line: list[int], name: str, payload: bytes, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, cells: dict[str, object], ticket: int, number: int, received: float) -> None:
    condition = cast(threading.Condition, cells["condition"])
    waiting = cast(list[int], cells["line"])
    counts = cast(dict[str, int], cells["counts"])
    times = cast(dict[str, float], cells["times"])
    try:
        try:
            response = _run_request(name, payload, request, context, arguments, cells, ticket, received)
        except Exception as error:
            response = _error_response(HsqlError_Crash(message=str(error)), 70)
        with condition:
            if ticket in waiting:
                waiting.remove(ticket)
                counts["queued"] -= 1
                condition.notify_all()
        with peer_condition:
            peer_condition.wait_for(lambda: _peer_first(peer_line, ticket))
        _deliver(peer, send_lock, response, context)
        elapsed = int((time.monotonic() - received) * 1000)
        _stderr(f"note: request {number}: exit {response.status} in {elapsed}ms\n")
    finally:
        with peer_condition:
            if ticket in peer_line:
                peer_line.remove(ticket)
            peer_condition.notify_all()
        with condition:
            if ticket in waiting:
                waiting.remove(ticket)
                counts["queued"] -= 1
            counts["inflight"] -= 1
            times["last"] = time.monotonic()
            condition.notify_all()


def _start_request_worker(peer: socket.socket, send_lock: threading.Lock, peer_condition: threading.Condition, peer_line: list[int], name: str, payload: bytes, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, cells: dict[str, object], ticket: int, number: int, received: float) -> None:
    threading.Thread(target=lambda: _request_worker(peer, send_lock, peer_condition, peer_line, name, payload, request, context, arguments, cells, ticket, number, received), daemon=True).start()


def _peer_done(peer_line: list[int]) -> bool:
    return not peer_line


def _cancel_request(payload: bytes, cells: dict[str, object]) -> None:
    wanted = payload.decode("utf-8", "replace").strip().lower()
    condition = cast(threading.Condition, cells["condition"])
    connections = cast(list[Connection], cells["connections"])
    counts = cast(dict[str, int], cells["counts"])
    with condition:
        active = connections[0] if wanted and cells["current"] == wanted and counts["busy"] and connections else None
        if active is not None:
            counts["cancelling"] += 1
    if active is not None:
        try:
            cancel_queries(active)
        finally:
            with condition:
                counts["cancelling"] -= 1
                condition.notify_all()


def _peer(peer: socket.socket, name: str, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, cells: dict[str, object]) -> None:
    send_lock = threading.Lock()
    peer_condition = threading.Condition()
    peer_line: list[int] = []
    condition = cast(threading.Condition, cells["condition"])
    counts = cast(dict[str, int], cells["counts"])
    times = cast(dict[str, float], cells["times"])
    waiting = cast(list[int], cells["line"])
    try:
        _send(peer, send_lock, _HELLO, HSQL_PROTOCOL_VERSION.encode("utf-8"))
        while True:
            with condition:
                if cells["stopping"] is True:
                    break
            frame = _read_frame(peer)
            if frame is None:
                break
            kind, payload = frame
            if kind == _STATUS:
                with condition:
                    status = _status_json(name, request, context, arguments, cells)
                _send(peer, send_lock, _STATUS, status)
            elif kind == _CANCEL:
                _cancel_request(payload, cells)
            elif kind == _REQUEST:
                with condition:
                    if cells["stopping"] is True:
                        break
                    counts["requests"] += 1
                    number = counts["requests"]
                    counts["inflight"] += 1
                    counts["queued"] += 1
                    ticket = counts["ticket"]
                    counts["ticket"] += 1
                    received = time.monotonic()
                    times["last"] = received
                    waiting.append(ticket)
                with peer_condition:
                    peer_line.append(ticket)
                try:
                    _start_request_worker(peer, send_lock, peer_condition, peer_line, name, payload, request, context, arguments, cells, ticket, number, received)
                except RuntimeError:
                    _request_worker(peer, send_lock, peer_condition, peer_line, name, payload, request, context, arguments, cells, ticket, number, received)
            else:
                break
    except OSError:
        return
    finally:
        with peer_condition:
            peer_condition.wait_for(lambda: _peer_done(peer_line))
        peer.close()
        with condition:
            peers = cast(list[socket.socket], cells["peers"])
            if peer in peers:
                peers.remove(peer)
            condition.notify_all()


def _peer_uid(peer: socket.socket) -> int | None:
    size = struct.calcsize("3i")
    try:
        credentials = peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, size)
    except OSError:
        return None
    if len(credentials) != size:
        return None
    _, uid, _ = cast(tuple[int, int, int], struct.unpack("3i", credentials))
    return uid


def _start_peer(peer: socket.socket, name: str, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, cells: dict[str, object]) -> None:
    threading.Thread(target=lambda: _peer(peer, name, request, context, arguments, cells), daemon=True).start()


def _should_stop(cells: dict[str, object], arguments: HsqlArguments, now: float) -> bool:
    counts = cast(dict[str, int], cells["counts"])
    times = cast(dict[str, float], cells["times"])
    if arguments.max_lifetime_seconds > 0 and now - times["started"] >= arguments.max_lifetime_seconds:
        return True
    return arguments.idle_timeout_seconds > 0 and counts["inflight"] == 0 and now - times["last"] >= arguments.idle_timeout_seconds


def _serve_loop(server: socket.socket, name: str, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, cells: dict[str, object]) -> None:
    condition = cast(threading.Condition, cells["condition"])
    while True:
        with condition:
            if _should_stop(cells, arguments, time.monotonic()):
                cells["stopping"] = True
                condition.notify_all()
                return
        try:
            peer, _ = server.accept()
        except TimeoutError:
            continue
        uid = _peer_uid(peer)
        if uid is None:
            _stderr("note: refused a connection whose owner could not be verified.\n")
            peer.close()
        elif uid != os.getuid():
            _stderr(f"note: refused a connection from uid {uid}, which is not yours.\n")
            peer.close()
        else:
            with condition:
                peers = cast(list[socket.socket], cells["peers"])
                peers.append(peer)
            try:
                _start_peer(peer, name, request, context, arguments, cells)
            except RuntimeError:
                with condition:
                    peers.remove(peer)
                peer.close()
                raise


def _all_done(cells: dict[str, object]) -> bool:
    counts = cast(dict[str, int], cells["counts"])
    return counts["inflight"] == 0 and counts["cancelling"] == 0


def _peers_done(cells: dict[str, object]) -> bool:
    peers = cast(list[socket.socket], cells["peers"])
    return not peers


def _close_peer(peer: socket.socket) -> None:
    try:
        peer.shutdown(socket.SHUT_RDWR)
    except OSError:
        peer.close()
        return
    peer.close()


def _finish(cells: dict[str, object], context: HsqlContext) -> None:
    condition = cast(threading.Condition, cells["condition"])
    connections = cast(list[Connection], cells["connections"])
    counts = cast(dict[str, int], cells["counts"])
    with condition:
        cells["stopping"] = True
        condition.notify_all()
        active = connections[0] if counts["busy"] and connections else None
    if active is not None:
        cancel_queries(active)
    with condition:
        condition.wait_for(lambda: _all_done(cells))
        remaining = connections.pop() if connections else None
        peers = list(cast(list[socket.socket], cells["peers"]))
    if remaining is not None:
        closed = close_connection(remaining)
        if not isinstance(closed, Ok):
            failure = closed.error
            _stderr(_redacted(f"note: {failure.title} {failure.message}\n", context))
    for peer in peers:
        _close_peer(peer)
    with condition:
        condition.wait_for(lambda: _peers_done(cells))


def serve_hsql_session(name: str, request: ConnectionRequest, context: HsqlContext, arguments: HsqlArguments, environment: FrozenMap[str, str]) -> I64:
    if not valid_session_name(name):
        return _usage(f"invalid session name '{name}': use 1 to 64 letters, digits, _ or -")
    if not sys.platform.startswith("linux"):
        return _usage(f"hsql --serve needs to verify which user connects to the session socket, which {sys.platform} does not support.")
    path = pathlib.Path(session_socket_path(name, environment, os.getuid()))
    problem = _check_directory(path.parent)
    if problem is not None:
        return _usage(problem)
    lock = filelock.FileLock(str(path.parent / f"{name}.lock"), timeout=0)
    try:
        lock.acquire(timeout=0)
    except filelock.Timeout:
        return _usage(f"session '{name}' is already running")
    except OSError as error:
        return _usage(f"could not lock session '{name}': {error}")
    try:
        problem = _remove_socket(path)
        if problem is not None:
            return _usage(problem)
        connection, failure_text = _open(request)
        if connection is None:
            _stderr(_redacted(f"hsql: error: {failure_text}\n", context))
            return 3
        now = time.monotonic()
        cells: dict[str, object] = {
            "connections": [connection], "adapter_names": CottList(values=_ADAPTERS.split(",")),
            "adapter_options": _options(request, context.adapter_name), "condition": threading.Condition(),
            "counts": {"requests": 0, "queued": 0, "busy": 0, "cancelling": 0, "inflight": 0, "ticket": 0},
            "times": {"started": now, "last": now}, "current": "", "stopping": False,
            "line": [], "peers": [],
        }
        ready = False
        startup_error: str | None = None
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
                server.bind(str(path))
                os.chmod(path, 0o600)
                server.listen(16)
                server.settimeout(0.2)
                ready = True
                _stderr(f"note: session '{name}' is ready ({context.adapter_name}). Send it queries with `hsql --session {name} -c ...`, or set HSQL_SESSION={name}. Ctrl-C stops it.\n")
                _serve_loop(server, name, request, context, arguments, cells)
        except KeyboardInterrupt:
            cells["stopping"] = True
        except (OSError, RuntimeError) as error:
            startup_error = f"could not start session '{name}': {error}"
        finally:
            _finish(cells, context)
            problem = _remove_socket(path)
            if problem is not None:
                _stderr(_redacted(f"note: {problem}\n", context))
        if startup_error is not None:
            return _usage(_redacted(startup_error, context))
        if ready:
            counts = cast(dict[str, int], cells["counts"])
            _stderr(f"note: session '{name}' stopped after {counts['requests']} request(s).\n")
        return 0
    finally:
        lock.release()
