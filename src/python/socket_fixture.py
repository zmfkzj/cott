# Compiler-owned finite framed AF_UNIX peer for contract-runner scenarios.
#
# The peer serves at most two connections on a private socket under the scenario
# root. Each served connection receives the authored greeting bytes, then the peer
# reads exactly one `u8 tag + big-endian u32 length` frame. Normal mode replies with
# the authored response bytes. Interrupt mode instead sends one SIGINT to this very
# process (confirmed through SO_PEERCRED) while armed, then serves one cancellation
# connection. Outbound bytes are finite authored data; nothing is executed.
#
# Standard library only. Imported names are private so this source can be embedded
# into the contract runner without rebinding runner globals.
import errno as _errno
import os as _os
import select as _select
import signal as _signal
import socket as _socket
import stat as _stat
import struct as _struct
import sys as _sys
import threading as _threading
import time as _time

# Bytes read for one inbound frame, header included.
_COTT_SOCKET_FRAME_LIMIT = 1 << 20
# Bytes of one authored greeting or response.
_COTT_SOCKET_OUTBOUND_LIMIT = 1 << 20
_COTT_SOCKET_CONNECTION_LIMIT = 2
_COTT_SOCKET_HEADER = _struct.Struct("!BI")
_COTT_SOCKET_PEERCRED = _struct.Struct("3i")
_COTT_SOCKET_CHUNK = 1 << 16
# Linux `struct sockaddr_un.sun_path` holds 108 bytes including the terminator.
_COTT_SOCKET_ADDRESS_LIMIT = 107
# Absent flags default to 0 so embedding never fails at import time elsewhere;
# `_require_platform` rejects every non-Linux platform before the flags are used.
_COTT_SOCKET_DIRECTORY_FLAGS = _os.O_RDONLY | sum(
    getattr(_os, name, 0) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")
)
_COTT_SOCKET_CONFIG_KEYS = frozenset(
    ("kind", "id", "path", "greeting", "response", "interrupt_after_request")
)
_COTT_SOCKET_METADATA_KEYS = frozenset(("span", "source_order"))


class FramedSocketFixtureError(AssertionError):
    """A socket fixture setup, protocol, signal-safety, or cleanup failure."""


class _CottSocketStop(Exception):
    """close() asked the worker to stop."""


def _cott_socket_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


class FramedSocketFixture:
    """A finite framed AF_UNIX peer bound under one scenario root.

    Lifecycle: ``start()`` once, ``arm()``/``disarm()`` around synchronous facade
    calls, ``close()`` exactly once at scenario end. ``events`` lists
    ``{"sequence", "kind", "bytes"}`` records with kinds ``socket.send``,
    ``socket.receive`` and ``socket.interrupt``; payloads and host paths are never
    recorded.
    """

    def __init__(self, config, root, limits):
        if not isinstance(config, dict):
            raise FramedSocketFixtureError("socket fixture config must be an object")
        fixture_id = config.get("id")
        if not isinstance(fixture_id, str) or not fixture_id:
            raise FramedSocketFixtureError("socket fixture config requires a non-empty string id")
        self._id = fixture_id
        keys = set(config)
        if not _COTT_SOCKET_CONFIG_KEYS <= keys:
            raise self._fail("config lacks " + ", ".join(sorted(_COTT_SOCKET_CONFIG_KEYS - keys)))
        unknown = keys - _COTT_SOCKET_CONFIG_KEYS - _COTT_SOCKET_METADATA_KEYS
        if unknown:
            raise self._fail("config has unsupported keys " + ", ".join(sorted(map(str, unknown))))
        if config["kind"] != "socket":
            raise self._fail("config kind must be `socket`")
        path = config["path"]
        if not isinstance(path, str) or not path or "\0" in path:
            raise self._fail("path must be a non-empty relative path")
        parts = path.split("/")
        if any(part in ("", ".", "..") for part in parts):
            raise self._fail("path must be normalized, relative and free of traversal")
        if any(len(_os.fsencode(part)) > 255 for part in parts):
            raise self._fail("path component exceeds 255 bytes")
        self._directories = tuple(parts[:-1])
        self._leaf = parts[-1]
        for key in ("greeting", "response"):
            value = config[key]
            if type(value) is not bytes:
                raise self._fail(f"{key} must be decoded bytes")
            if len(value) > _COTT_SOCKET_OUTBOUND_LIMIT:
                raise self._fail(f"{key} exceeds the 1 MiB limit")
        self._greeting = config["greeting"]
        self._response = config["response"]
        if type(config["interrupt_after_request"]) is not bool:
            raise self._fail("interrupt_after_request must be a boolean")
        self._interrupt = config["interrupt_after_request"]

        if not isinstance(limits, dict):
            raise self._fail("limits must be an object")
        timeout_ms = limits.get("scenario_timeout_ms")
        if not _cott_socket_int(timeout_ms) or timeout_ms <= 0:
            raise self._fail("limits.scenario_timeout_ms must be a positive integer")
        event_limit = limits.get("transcript_events")
        if not _cott_socket_int(event_limit) or event_limit < 0:
            raise self._fail("limits.transcript_events must be a non-negative integer")
        self._timeout = timeout_ms / 1000
        self._event_limit = event_limit

        try:
            root = _os.fspath(root)
        except TypeError:
            root = None
        if not isinstance(root, str) or not _os.path.isabs(root):
            raise self._fail("scenario root must be an absolute path")
        self._root = root

        self._lock = _threading.Lock()
        self._events = []
        self._state = "new"
        self._armed = False
        self._interrupted = False
        self._pid = None
        self._parent_fd = None
        self._inode = None
        self._listener = None
        self._wake = None
        self._thread = None
        self._error = None

    @property
    def events(self):
        with self._lock:
            return [dict(event) for event in self._events]

    def start(self):
        if self._state != "new":
            raise self._fail("fixture can start only once")
        self._state = "starting"
        try:
            self._require_platform()
            self._pid = _os.getpid()
            self._parent_fd = self._open_parent()
            self._listener = self._bind()
            self._listener.listen(_COTT_SOCKET_CONNECTION_LIMIT)
            self._listener.setblocking(False)
            self._wake = _os.pipe()
            _os.set_blocking(self._wake[1], False)
            self._thread = _threading.Thread(target=self._serve, name="cott-socket-fixture", daemon=True)
            self._thread.start()
            self._state = "started"
        except BaseException as error:
            self._state = "closed"
            stopped = True
            if self._thread is not None:
                self._wake_worker()
                self._join_worker(_time.monotonic() + self._timeout)
                stopped = not self._thread.is_alive()
            failures = self._release(stopped)
            if not stopped:
                failures.insert(0, self._fail("worker did not stop within scenario_timeout_ms"))
            if failures:
                raise failures[0] from error
            raise

    def arm(self):
        with self._lock:
            if self._state != "started":
                raise self._fail("fixture must be started and open to arm")
            if self._armed:
                raise self._fail("fixture is already armed")
            if self._interrupt:
                if _threading.current_thread() is not _threading.main_thread():
                    raise self._fail("interrupt fixture must be armed from the main thread")
                if _os.getpid() != self._pid:
                    raise self._fail("interrupt fixture armed outside the process that started it")
                if _signal.getsignal(_signal.SIGINT) is not _signal.default_int_handler:
                    raise self._fail("installed SIGINT handler is not Python's KeyboardInterrupt handler")
                if _signal.SIGINT in _signal.pthread_sigmask(_signal.SIG_BLOCK, ()):
                    raise self._fail("SIGINT is blocked in the main thread")
            self._armed = True

    def disarm(self):
        with self._lock:
            self._armed = False

    def close(self):
        if self._state == "new":
            self._state = "closed"
            return
        if self._state != "started":
            return
        self._state = "closing"
        failures = []
        deadline = _time.monotonic() + self._timeout
        # Disarm strictly before any descriptor is closed. Each step is idempotent: a
        # SIGINT this fixture already sent may still surface as KeyboardInterrupt here,
        # and since it never sends a second one, retrying the step terminates.
        for step in (self.disarm, lambda: self._finish_exchange(deadline), self._wake_worker, lambda: self._join_worker(deadline)):
            while True:
                try:
                    step()
                    break
                except KeyboardInterrupt as error:
                    failures.append(error)
                except BaseException as error:
                    failures.append(error)
                    break
        stopped = not self._thread.is_alive()
        if not stopped:
            # Worker-owned descriptors stay open rather than racing a live thread.
            failures.append(self._fail("worker did not stop within scenario_timeout_ms"))
        elif self._error is not None:
            failures.insert(0, self._error)
        failures.extend(self._release(stopped))
        self._state = "closed"
        if len(failures) == 1:
            raise failures[0]
        if failures:
            details = "; ".join(
                str(failure) if isinstance(failure, FramedSocketFixtureError) else type(failure).__name__
                for failure in failures
            )
            raise self._fail(f"{len(failures)} failures: {details}") from failures[0]

    def _fail(self, message):
        return FramedSocketFixtureError(f"socket fixture `{self._id}`: {message}")

    def _wake_worker(self):
        try:
            _os.write(self._wake[1], b"\0")
        except BlockingIOError:
            pass

    def _finish_exchange(self, deadline):
        # The client returns after sending CANCEL, not after the peer has drained
        # it. Complete that bounded second frame before requesting worker stop.
        if self._interrupted:
            self._join_worker(deadline)

    def _join_worker(self, deadline):
        while self._thread.is_alive():
            remaining = deadline - _time.monotonic()
            if remaining <= 0:
                return
            self._thread.join(remaining)

    def _require_platform(self):
        if not _sys.platform.startswith("linux"):
            raise self._fail("requires Linux AF_UNIX sockets with SO_PEERCRED")
        for owner, name in (
            (_socket, "AF_UNIX"),
            (_socket, "SO_PEERCRED"),
            (_socket, "MSG_NOSIGNAL"),
            (_select, "poll"),
            (_signal, "SIGINT"),
            (_signal, "pthread_sigmask"),
        ):
            if getattr(owner, name, None) is None:
                raise self._fail(f"platform lacks {owner.__name__}.{name}")

    def _open_parent(self):
        euid = _os.geteuid()
        try:
            fd = _os.open(self._root, _COTT_SOCKET_DIRECTORY_FLAGS)
        except OSError as error:
            # Keep the host path out of the error chain; the errno names the cause.
            reason = _errno.errorcode.get(error.errno, str(error.errno))
            raise self._fail(f"scenario root is not an openable non-symlink directory ({reason})") from None
        try:
            self._require_owned_directory(fd, euid)
            for part in self._directories:
                created = False
                try:
                    _os.mkdir(part, 0o700, dir_fd=fd)
                    created = True
                except FileExistsError:
                    pass
                try:
                    child = _os.open(part, _COTT_SOCKET_DIRECTORY_FLAGS, dir_fd=fd)
                except OSError as error:
                    raise self._fail("path component is a symlink or not a directory") from error
                previous, fd = fd, child
                _os.close(previous)
                self._require_owned_directory(fd, euid)
                if created:
                    _os.fchmod(fd, 0o700)
            if _os.fstat(fd).st_mode & 0o022:
                raise self._fail("socket parent directory is writable by group or others")
            return fd
        except BaseException:
            _os.close(fd)
            raise

    def _require_owned_directory(self, fd, euid):
        status = _os.fstat(fd)
        if not _stat.S_ISDIR(status.st_mode) or status.st_uid != euid:
            raise self._fail("socket directory is not owned by the runner")

    def _bind(self):
        try:
            _os.lstat(self._leaf, dir_fd=self._parent_fd)
        except FileNotFoundError:
            pass
        else:
            raise self._fail("socket target already exists")
        address = f"/proc/self/fd/{self._parent_fd}/{self._leaf}"
        if len(_os.fsencode(address)) > _COTT_SOCKET_ADDRESS_LIMIT:
            raise self._fail("socket file name is too long for AF_UNIX")
        listener = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        try:
            # Linux creates the bound inode with the socket inode's mode minus umask.
            _os.fchmod(listener.fileno(), 0o600)
            try:
                listener.bind(address)
            except OSError as error:
                raise self._fail("cannot bind the socket inside its private directory") from error
            status = _os.lstat(self._leaf, dir_fd=self._parent_fd)
            if not _stat.S_ISSOCK(status.st_mode) or status.st_uid != _os.geteuid():
                raise self._fail("bound path is not a socket owned by the runner")
            self._inode = (status.st_dev, status.st_ino)
            if _stat.S_IMODE(status.st_mode) != 0o600:
                raise self._fail("bound socket is not mode 0600")
            return listener
        except BaseException:
            listener.close()
            raise

    def _release(self, stopped=True):
        failures = []
        if stopped:
            if self._listener is not None:
                try:
                    self._listener.close()
                except OSError as error:
                    failures.append(error)
            if self._wake is not None:
                for fd in self._wake:
                    try:
                        _os.close(fd)
                    except OSError as error:
                        failures.append(error)
                self._wake = None
        if self._inode is not None:
            inode, self._inode = self._inode, None
            try:
                status = _os.lstat(self._leaf, dir_fd=self._parent_fd)
            except FileNotFoundError:
                status = None
            except OSError as error:
                failures.append(error)
                status = None
            if status is not None:
                if _stat.S_ISSOCK(status.st_mode) and (status.st_dev, status.st_ino) == inode:
                    try:
                        _os.unlink(self._leaf, dir_fd=self._parent_fd)
                    except FileNotFoundError:
                        pass
                    except OSError as error:
                        failures.append(error)
                else:
                    failures.append(self._fail("socket path was replaced; left untouched"))
        if self._parent_fd is not None:
            fd, self._parent_fd = self._parent_fd, None
            try:
                _os.close(fd)
            except OSError as error:
                failures.append(error)
        return failures

    def _serve(self):
        connections = []
        try:
            # Keep SIGINT off this thread so a process-directed signal reaches the main thread.
            _signal.pthread_sigmask(_signal.SIG_BLOCK, {_signal.SIGINT})
            first = self._accept(connections, None)
            deadline = _time.monotonic() + self._timeout
            peer = self._peer(first)
            self._send(first, self._greeting, deadline)
            if not self._receive_frame(first, deadline):
                return
            if not self._interrupt:
                self._send(first, self._response, deadline)
                return
            self._signal_runner(peer)
            second = self._accept(connections, deadline)
            self._peer(second)
            self._send(second, self._greeting, deadline)
            if not self._receive_frame(second, deadline):
                raise self._fail("cancellation connection closed without a frame")
        except _CottSocketStop:
            pass
        except BaseException as error:
            self._error = error
        finally:
            # Closing the listener refuses further connections; closing a connection
            # releases a client still waiting for bytes.
            for sock in (*connections, self._listener):
                try:
                    sock.close()
                except OSError as error:
                    if self._error is None:
                        self._error = error

    def _record_locked(self, kind, count):
        if len(self._events) >= self._event_limit:
            raise self._fail("socket transcript exceeds limits.transcript_events")
        self._events.append({"sequence": len(self._events), "kind": kind, "bytes": count})

    def _record(self, kind, count):
        with self._lock:
            self._record_locked(kind, count)

    def _signal_runner(self, peer):
        with self._lock:
            if not self._armed:
                raise self._fail("request completed while disarmed; SIGINT not sent")
            if self._interrupted:
                raise self._fail("SIGINT was already sent")
            pid = _os.getpid()
            if pid != self._pid or peer != pid:
                raise self._fail("peer is not this contract-runner process; SIGINT not sent")
            if _signal.getsignal(_signal.SIGINT) is not _signal.default_int_handler:
                raise self._fail("installed SIGINT handler is not Python's KeyboardInterrupt handler")
            if len(self._events) >= self._event_limit:
                raise self._fail("socket transcript exceeds limits.transcript_events")
            self._interrupted = True
            _os.kill(pid, _signal.SIGINT)
            self._record_locked("socket.interrupt", 0)

    def _wait(self, sock, events, deadline):
        poller = _select.poll()
        poller.register(self._wake[0], _select.POLLIN)
        poller.register(sock, events)
        while True:
            if deadline is None:
                timeout = None
            else:
                remaining = deadline - _time.monotonic()
                if remaining <= 0:
                    raise self._fail("socket exchange exceeded limits.scenario_timeout_ms")
                timeout = int(remaining * 1000) + 1
            ready = poller.poll(timeout)
            if any(fd == self._wake[0] for fd, _ in ready):
                raise _CottSocketStop()
            if ready:
                return

    def _accept(self, connections, deadline):
        budget = _COTT_SOCKET_CONNECTION_LIMIT if self._interrupt else 1
        if len(connections) >= budget:
            raise self._fail("connection limit exceeded")
        while True:
            self._wait(self._listener, _select.POLLIN, deadline)
            try:
                connection, _ = self._listener.accept()
            except (BlockingIOError, InterruptedError, ConnectionAbortedError):
                continue
            connections.append(connection)
            connection.setblocking(False)
            if len(connections) == budget:
                # Refuse later connections before this one is answered, so a client
                # that reconnects after its reply deterministically sees ECONNREFUSED.
                self._listener.close()
            return connection

    def _peer(self, connection):
        raw = connection.getsockopt(_socket.SOL_SOCKET, _socket.SO_PEERCRED, _COTT_SOCKET_PEERCRED.size)
        pid, uid, _ = _COTT_SOCKET_PEERCRED.unpack(raw)
        if pid <= 0 or pid != self._pid or pid != _os.getpid() or uid != _os.geteuid():
            raise self._fail("peer is not this contract-runner process")
        return pid

    def _send(self, connection, data, deadline):
        view = memoryview(data)
        sent = 0
        while sent < len(view):
            self._wait(connection, _select.POLLOUT, deadline)
            try:
                sent += connection.send(view[sent:], _socket.MSG_NOSIGNAL)
            except (BlockingIOError, InterruptedError):
                continue
            except OSError as error:
                raise self._fail("peer closed before the authored bytes were delivered") from error
        self._record("socket.send", len(view))

    def _receive_into(self, connection, view, deadline):
        count = 0
        while count < len(view):
            self._wait(connection, _select.POLLIN, deadline)
            try:
                received = connection.recv_into(view[count:])
            except (BlockingIOError, InterruptedError):
                continue
            except ConnectionResetError:
                break
            except OSError as error:
                raise self._fail("peer connection failed while receiving") from error
            if received == 0:
                break
            count += received
        return count

    def _receive_frame(self, connection, deadline):
        """Read one bounded frame; False when the peer closed at a frame boundary."""
        header = bytearray(_COTT_SOCKET_HEADER.size)
        received = self._receive_into(connection, memoryview(header), deadline)
        if received == 0:
            return False
        if received < len(header):
            raise self._fail("peer closed inside a frame header")
        _, length = _COTT_SOCKET_HEADER.unpack(header)
        total = len(header) + length
        if total > _COTT_SOCKET_FRAME_LIMIT:
            raise self._fail("inbound frame exceeds the 1 MiB limit")
        view = memoryview(bytearray(min(length, _COTT_SOCKET_CHUNK)))
        remaining = length
        while remaining:
            size = min(remaining, len(view))
            if self._receive_into(connection, view[:size], deadline) < size:
                raise self._fail("peer closed inside a frame payload")
            remaining -= size
        self._record("socket.receive", total)
        return True
