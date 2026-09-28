"""Compiler-owned database fixtures for contract scenarios.

A SQLite or DuckDB fixture owns a fresh private directory and projects confined file paths into it; the public
facade under test opens its own real connection there (in-memory databases use the authored `:memory:` input,
not this fixture). A PostgreSQL fixture provisions a disposable cluster inside its private directory with the
native toolchain the host froze and mounted, serves it only on a private Unix socket, and tears it down.

The host validates the fixture declaration, freezes the toolchain, mounts its loader libraries (forwarded here
only through LD_LIBRARY_PATH) and records provenance; this module never reads tool versions or hashes and never
widens sandbox limits. Standard library only. Every subprocess, readiness and shutdown wait is bounded by the
scenario timeout, and failures are raised as DatabaseFixtureError, never as clause observations.
"""
import os
import pathlib
import posixpath
import shutil
import signal
import socket
import stat
import struct
import subprocess
import time
import urllib.parse

_DATABASE_FIXTURE_KEYS = frozenset(("kind", "id", "backend"))
_DATABASE_FIXTURE_METADATA = frozenset(("span", "source_order"))
_DATABASE_FIXTURE_BACKENDS = ("sqlite", "duckdb", "postgres")
_DATABASE_FIXTURE_LIMITS = ("scenario_timeout_ms", "filesystem_bytes", "filesystem_files")
_POSTGRES_TOOLCHAIN_KEYS = frozenset(("initdb", "postgres", "share"))
_POSTGRES_USER = "cott_fixture"
_POSTGRES_DATABASE = "postgres"
_POSTGRES_PORT = 5432
# Linux sockaddr_un.sun_path holds 108 bytes including the terminating NUL.
_POSTGRES_SOCKET_PATH_MAX = 107
# Explicit native settings. initdb installs them (so bootstrap also keeps dynamic shared memory inside the
# cluster) and the server command line repeats them, which outranks every configuration file.
_POSTGRES_SETTINGS = (
    ("listen_addresses", ""),
    ("unix_socket_permissions", "0700"),
    ("max_connections", "4"),
    ("superuser_reserved_connections", "0"),
    ("shared_buffers", "8MB"),
    ("dynamic_shared_memory_type", "mmap"),
    ("autovacuum", "off"),
    ("jit", "off"),
    ("max_parallel_workers", "0"),
    ("max_parallel_workers_per_gather", "0"),
    ("max_parallel_maintenance_workers", "0"),
    ("min_wal_size", "2MB"),
    ("max_wal_size", "16MB"),
    ("fsync", "on"),
)
_POSTGRES_PROTOCOL = 196608  # frontend/backend protocol 3.0
_POSTGRES_CANNOT_CONNECT_NOW = "57P03"
_POSTGRES_MESSAGE_LIMIT = 65536
_LOG_TAIL_BYTES = 1024
_POLL_SECONDS = 0.02


class DatabaseFixtureError(Exception):
    """A database fixture configuration, setup, projection or cleanup failure; never a clause observation."""

    def __init__(self, fixture_id, phase, detail):
        super().__init__(f"database fixture `{fixture_id}` {phase} failed: {detail}")
        self.fixture_id = fixture_id
        self.phase = phase
        self.detail = detail


class DatabaseFixture:
    """One scenario database fixture: start(), then path()/url() projections, then close()."""

    def __init__(self, config, root, limits, postgres_toolchain=None):
        self._id = config.get("id") if isinstance(config, dict) and isinstance(config.get("id"), str) else "?"
        if not isinstance(config, dict):
            raise self._error("configuration", "declaration must be an object")
        unsupported = sorted(set(config) - _DATABASE_FIXTURE_KEYS - _DATABASE_FIXTURE_METADATA)
        if unsupported:
            raise self._error("configuration", f"unsupported settings {', '.join(map(repr, unsupported))}")
        missing = sorted(_DATABASE_FIXTURE_KEYS - set(config))
        if missing:
            raise self._error("configuration", f"missing settings {', '.join(map(repr, missing))}")
        if config["kind"] != "database":
            raise self._error("configuration", f"kind must be 'database', got {config['kind']!r}")
        if not isinstance(config["id"], str) or not config["id"]:
            raise self._error("configuration", "id must be a non-empty string")
        backend = config["backend"]
        if backend not in _DATABASE_FIXTURE_BACKENDS:
            raise self._error(
                "configuration",
                f"backend must be one of {', '.join(_DATABASE_FIXTURE_BACKENDS)}, got {backend!r}",
            )
        self._backend = backend
        root = os.fspath(root) if isinstance(root, (str, os.PathLike)) else root
        if not isinstance(root, str) or not os.path.isabs(root) or os.path.normpath(root) != root or "\0" in root:
            raise self._error("configuration", f"fixture root must be an absolute normalized path, got {root!r}")
        self._root = root
        if not isinstance(limits, dict):
            raise self._error("configuration", "scenario limits must be an object")
        for name in _DATABASE_FIXTURE_LIMITS:
            value = limits.get(name)
            if type(value) is not int or value < 1:
                raise self._error("configuration", f"scenario limit {name} must be a positive integer, got {value!r}")
        self._timeout = limits["scenario_timeout_ms"] / 1000
        self._timeout_ms = limits["scenario_timeout_ms"]
        self._filesystem_bytes = limits["filesystem_bytes"]
        self._filesystem_files = limits["filesystem_files"]
        if backend == "postgres":
            if not isinstance(postgres_toolchain, dict):
                raise self._error("configuration", "a postgres fixture requires the host-frozen postgres_toolchain")
            keys = set(postgres_toolchain)
            if keys != _POSTGRES_TOOLCHAIN_KEYS:
                raise self._error(
                    "configuration",
                    f"postgres_toolchain must have exactly the keys initdb, postgres, share; got {sorted(keys)!r}",
                )
            for name in sorted(_POSTGRES_TOOLCHAIN_KEYS):
                value = postgres_toolchain[name]
                if not isinstance(value, str) or not os.path.isabs(value) or "\0" in value:
                    raise self._error("configuration", f"postgres_toolchain {name} must be an absolute path, got {value!r}")
            self._toolchain = dict(postgres_toolchain)
        elif postgres_toolchain is not None:
            raise self._error("configuration", f"postgres_toolchain applies only to postgres fixtures, not {backend}")
        else:
            self._toolchain = None
        self._state = "new"
        self._root_created = False
        self._root_identity = None
        self._initdb = None
        self._server = None
        self._url = None
        self._filesystem_usage = (0, 0)

    def start(self):
        """Create the private root and, for PostgreSQL, a ready server; any failure is cleaned up first."""
        if self._state != "new":
            raise self._error("setup", f"fixture is {self._state}; each fixture starts once")
        self._state = "starting"
        deadline = time.monotonic() + self._timeout
        try:
            if self._backend == "postgres":
                self._check_postgres_prerequisites()
            self._create_root()
            if self._backend == "postgres":
                self._start_postgres(deadline)
        except BaseException as error:
            problems = self._teardown(audit=False)
            self._state = "closed"
            if not isinstance(error, Exception):
                raise
            if isinstance(error, DatabaseFixtureError):
                detail = error.detail
            elif isinstance(error, OSError) and error.filename is not None:
                detail = f"{error.strerror or error} ({error.filename})"
            else:
                detail = f"{type(error).__name__}: {error}"
            if problems:
                detail = f"{detail}; cleanup also failed: {'; '.join(problems)}"
            if isinstance(error, DatabaseFixtureError) and not problems:
                raise
            raise self._error("setup", detail) from error
        self._state = "started"

    def close(self):
        """Stop owned processes, enforce the filesystem bounds, and remove the private root. Idempotent."""
        if self._state in ("new", "closed"):
            self._state = "closed"
            return
        started = self._state == "started"
        self._state = "closed"
        problems = self._teardown(audit=started)
        if problems:
            raise self._error("cleanup", "; ".join(problems))

    @property
    def filesystem_usage(self):
        """Final pre-removal (file count, byte count), valid after successful close()."""
        return self._filesystem_usage

    def path(self, relative):
        """Project a relative file path into the private root of a SQLite or DuckDB fixture."""
        phase = "path projection"
        if self._backend == "postgres":
            raise self._error(phase, "a postgres fixture exposes its server through url('/'), not file paths")
        if self._state != "started":
            raise self._error(phase, f"fixture is not started (state {self._state})")
        if not isinstance(relative, str):
            raise self._error(phase, f"path must be a string, got {type(relative).__name__}")
        if relative == ":memory:":
            raise self._error(phase, "in-memory databases use the authored `:memory:` input, not a fixture path")
        if not relative or "\0" in relative or "\\" in relative or relative.startswith("/"):
            raise self._error(phase, f"{relative!r} is not a relative `/`-separated path")
        normalized = posixpath.normpath(relative)
        if normalized in (".", "..") or normalized.startswith("../"):
            raise self._error(phase, f"{relative!r} does not name a file inside the private fixture root")
        if normalized != relative:
            raise self._error(phase, f"{relative!r} is not a normalized relative path")
        parts = normalized.split("/")
        current = self._root
        self._require_real_directory(phase, current)
        for index, part in enumerate(parts):
            current = os.path.join(current, part)
            try:
                status = os.lstat(current)
            except FileNotFoundError:
                break
            if stat.S_ISLNK(status.st_mode):
                raise self._error(phase, f"{relative!r} traverses symlink `{current}`")
            last = index == len(parts) - 1
            if not last and not stat.S_ISDIR(status.st_mode):
                raise self._error(phase, f"{relative!r} traverses non-directory `{current}`")
            if last and not stat.S_ISREG(status.st_mode):
                raise self._error(phase, f"{relative!r} names `{current}`, which is not a regular file")
        return pathlib.Path(self._root, *parts)

    def url(self, route):
        """The libpq URI of a PostgreSQL fixture's private Unix socket; only route `/` exists."""
        phase = "url projection"
        if self._backend != "postgres":
            raise self._error(phase, f"a {self._backend} fixture exposes file paths through path(...), not URLs")
        if self._state != "started":
            raise self._error(phase, f"fixture is not started (state {self._state})")
        if route != "/":
            raise self._error(phase, f"a postgres fixture serves only route '/', got {route!r}")
        return self._url

    def _error(self, phase, detail):
        return DatabaseFixtureError(self._id, phase, detail)

    def _remaining(self, deadline):
        return max(0.0, deadline - time.monotonic())

    def _require_real_directory(self, phase, path):
        try:
            status = os.lstat(path)
        except OSError as error:
            raise self._error(phase, f"private fixture root `{path}` is unavailable: {error.strerror}") from error
        if not stat.S_ISDIR(status.st_mode):
            raise self._error(phase, f"private fixture root `{path}` is no longer a real directory")
        if path == self._root and self._root_identity is not None:
            if (status.st_dev, status.st_ino) != self._root_identity:
                raise self._error(phase, "private fixture root identity changed")

    def _check_postgres_prerequisites(self):
        if os.geteuid() == 0:
            raise self._error(
                "setup",
                "PostgreSQL initdb and postgres refuse to run as UID 0; run the contract runner as an unprivileged user",
            )
        for name in ("initdb", "postgres"):
            path = self._toolchain[name]
            try:
                status = os.stat(path)
            except OSError as error:
                raise self._error("setup", f"PostgreSQL {name} not found at `{path}`: {error.strerror}") from error
            if not stat.S_ISREG(status.st_mode) or not os.access(path, os.X_OK):
                raise self._error("setup", f"PostgreSQL {name} at `{path}` is not an executable file")
        # initdb runs the backend that sits beside its own resolved executable.
        beside = os.path.join(os.path.dirname(os.path.realpath(self._toolchain["initdb"])), "postgres")
        if os.path.realpath(self._toolchain["postgres"]) != os.path.realpath(beside):
            raise self._error(
                "setup",
                f"PostgreSQL postgres `{self._toolchain['postgres']}` is not the backend `{beside}` that initdb runs",
            )
        share = self._toolchain["share"]
        if not os.path.isdir(share):
            raise self._error("setup", f"PostgreSQL share directory `{share}` does not exist")
        if not os.path.isfile(os.path.join(share, "postgres.bki")):
            raise self._error("setup", f"PostgreSQL share directory `{share}` lacks postgres.bki")
        socket_path = os.path.join(self._root, "socket", f".s.PGSQL.{_POSTGRES_PORT}")
        length = len(os.fsencode(socket_path))
        if length > _POSTGRES_SOCKET_PATH_MAX:
            raise self._error(
                "setup",
                f"PostgreSQL socket path `{socket_path}` is {length} bytes; Unix sockets allow at most "
                f"{_POSTGRES_SOCKET_PATH_MAX}; use a shorter fixture root",
            )

    def _create_root(self):
        parent = os.path.dirname(self._root)
        if not os.path.isdir(parent):
            raise self._error("setup", f"fixture root parent `{parent}` is not an existing directory")
        if os.path.realpath(parent) != parent:
            raise self._error("setup", "fixture root parent traverses a symlink")
        try:
            os.mkdir(self._root, 0o700)
        except FileExistsError as error:
            raise self._error(
                "setup", f"fixture root `{self._root}` already exists; a database fixture owns a fresh private directory"
            ) from error
        self._root_created = True
        os.chmod(self._root, 0o700)
        status = os.lstat(self._root)
        self._root_identity = (status.st_dev, status.st_ino)
        if not stat.S_ISDIR(status.st_mode) or status.st_uid != os.geteuid():
            raise self._error("setup", f"fixture root `{self._root}` is not a directory owned by this runner")

    def _settings(self):
        return _POSTGRES_SETTINGS + (("temp_file_limit", f"{max(1, self._filesystem_bytes // 1024)}kB"),)

    def _environment(self):
        environment = {"LANG": "C", "LC_ALL": "C", "TZ": "UTC"}
        library_path = os.environ.get("LD_LIBRARY_PATH")
        if library_path:
            environment["LD_LIBRARY_PATH"] = library_path
        return environment

    def _spawn(self, argv, log_name):
        log = os.open(
            os.path.join(self._root, log_name),
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
        )
        try:
            return subprocess.Popen(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                cwd=self._root,
                env=self._environment(),
                start_new_session=True,
            )
        finally:
            os.close(log)

    def _log_tail(self, log_name):
        try:
            descriptor = os.open(os.path.join(self._root, log_name), os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        except OSError as error:
            return f"<{log_name} unavailable: {error.strerror}>"
        with os.fdopen(descriptor, "rb") as log:
            size = os.fstat(log.fileno()).st_size
            log.seek(max(0, size - _LOG_TAIL_BYTES))
            tail = log.read(_LOG_TAIL_BYTES).decode("utf-8", "replace").strip()
        return tail or f"<{log_name} is empty>"

    def _start_postgres(self, deadline):
        data = os.path.join(self._root, "data")
        socket_directory = os.path.join(self._root, "socket")
        settings = self._settings()
        initdb = [
            self._toolchain["initdb"],
            "--pgdata", data,
            "-L", self._toolchain["share"],
            "--username", _POSTGRES_USER,
            "--auth-local", "trust",
            "--auth-host", "reject",
            "--encoding", "UTF8",
            "--locale", "C",
            "--wal-segsize", "1",
            "--no-sync",
            "--no-instructions",
        ]
        for name, value in settings:
            initdb += ["--set", f"{name}={value}"]
        self._initdb = self._spawn(initdb, "initdb.log")
        try:
            status = self._initdb.wait(timeout=self._remaining(deadline))
        except subprocess.TimeoutExpired as error:
            raise self._error(
                "setup", f"initdb did not finish within the {self._timeout_ms} ms scenario timeout"
            ) from error
        self._initdb = None
        if status != 0:
            outcome = f"was killed by signal {-status}" if status < 0 else f"exited with status {status}"
            raise self._error("setup", f"initdb {outcome}: {self._log_tail('initdb.log')}")
        self._audit("setup")
        os.mkdir(socket_directory, 0o700)
        os.chmod(socket_directory, 0o700)
        server = [
            self._toolchain["postgres"],
            "-D", data,
            # A quoted entry keeps commas or spaces in the root from splitting unix_socket_directories.
            "-k", '"' + socket_directory.replace('"', '""') + '"',
            "-p", str(_POSTGRES_PORT),
        ]
        for name, value in settings:
            server += ["-c", f"{name}={value}"]
        self._server = self._spawn(server, "postgres.log")
        self._await_ready(os.path.join(socket_directory, f".s.PGSQL.{_POSTGRES_PORT}"), deadline)
        host = urllib.parse.quote(socket_directory, safe="")
        self._url = f"postgresql://{_POSTGRES_USER}@{host}:{_POSTGRES_PORT}/{_POSTGRES_DATABASE}"

    def _await_ready(self, socket_path, deadline):
        waiting = "the server socket has not appeared"
        while True:
            status = self._server.poll()
            if status is not None:
                raise self._error(
                    "setup",
                    f"PostgreSQL server exited with status {status} before accepting the fixture database: "
                    f"{self._log_tail('postgres.log')}",
                )
            remaining = self._remaining(deadline)
            if remaining <= 0:
                raise self._error(
                    "setup",
                    f"PostgreSQL did not accept the fixture database within the {self._timeout_ms} ms scenario "
                    f"timeout ({waiting}): {self._log_tail('postgres.log')}",
                )
            ready, waiting = self._handshake(socket_path, remaining)
            if ready:
                return
            time.sleep(min(_POLL_SECONDS, self._remaining(deadline)))

    def _handshake(self, socket_path, timeout):
        """Run a PostgreSQL startup for the fixture role and database; (True, None) once it is ready for queries."""
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            connection.settimeout(timeout)
            try:
                connection.connect(socket_path)
            except (FileNotFoundError, ConnectionRefusedError, BlockingIOError) as error:
                return False, f"socket not accepting connections: {error.strerror}"
            parameters = (
                b"user\0" + _POSTGRES_USER.encode() + b"\0database\0" + _POSTGRES_DATABASE.encode() + b"\0\0"
            )
            body = struct.pack("!I", _POSTGRES_PROTOCOL) + parameters
            connection.sendall(struct.pack("!I", len(body) + 4) + body)
            authenticated = False
            while True:
                header = self._receive(connection, 5)
                kind = header[:1]
                (length,) = struct.unpack("!I", header[1:])
                if length < 4 or length > _POSTGRES_MESSAGE_LIMIT:
                    raise self._error("setup", f"PostgreSQL startup sent a malformed {kind!r} message")
                payload = self._receive(connection, length - 4)
                if kind == b"R":
                    code = struct.unpack("!I", payload[:4])[0] if len(payload) >= 4 else None
                    if code != 0:
                        raise self._error(
                            "setup",
                            f"PostgreSQL requested authentication method {code} for `{_POSTGRES_USER}` "
                            "instead of local trust",
                        )
                    authenticated = True
                elif kind == b"E":
                    fields = {}
                    for field in payload.split(b"\0"):
                        if field:
                            fields[field[:1].decode("ascii", "replace")] = field[1:].decode("utf-8", "replace")
                    if fields.get("C") == _POSTGRES_CANNOT_CONNECT_NOW:
                        return False, fields.get("M", "the database system is starting up")
                    raise self._error(
                        "setup",
                        f"PostgreSQL refused the fixture database: {fields.get('S', 'ERROR')} "
                        f"{fields.get('C', '?')} {fields.get('M', '')}",
                    )
                elif kind == b"Z":
                    if not authenticated:
                        raise self._error("setup", "PostgreSQL reported ready before authenticating the fixture role")
                    try:
                        connection.sendall(b"X\0\0\0\x04")
                    except OSError:
                        pass  # The session was proven ready; Terminate is only a courtesy.
                    return True, None
                elif kind not in (b"S", b"K", b"N"):
                    raise self._error("setup", f"PostgreSQL startup sent unexpected message {kind!r}")
        except (socket.timeout, ConnectionError) as error:
            return False, f"startup handshake interrupted: {error}"
        finally:
            connection.close()

    def _receive(self, connection, size):
        chunks = []
        while size:
            chunk = connection.recv(size)
            if not chunk:
                raise ConnectionError("server closed the connection")
            chunks.append(chunk)
            size -= len(chunk)
        return b"".join(chunks)

    def _audit(self, phase):
        files = 0
        size = 0
        pending = [self._root]
        while pending:
            with os.scandir(pending.pop()) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink():
                            raise self._error(phase, f"fixture root contains symlink `{entry.path}`")
                        if entry.is_dir(follow_symlinks=False):
                            pending.append(entry.path)
                        elif entry.is_file(follow_symlinks=False):
                            files += 1
                            size += entry.stat(follow_symlinks=False).st_size
                    except FileNotFoundError:
                        continue
                    if files > self._filesystem_files:
                        raise self._error(
                            phase, f"fixture root holds more than the filesystem_files limit of {self._filesystem_files} files"
                        )
                    if size > self._filesystem_bytes:
                        raise self._error(
                            phase, f"fixture root holds more than the filesystem_bytes limit of {self._filesystem_bytes} bytes"
                        )
        return files, size

    def _teardown(self, audit):
        problems = []
        if self._initdb is not None:
            problems += self._kill_initdb()
            self._initdb = None
        if self._server is not None:
            problems += self._stop_server()
            self._server = None
        self._url = None
        if self._root_created:
            try:
                self._require_real_directory("cleanup", self._root)
            except DatabaseFixtureError as error:
                problems.append(error.detail)
                return problems
            if audit and not problems:
                try:
                    self._filesystem_usage = self._audit("cleanup")
                except DatabaseFixtureError as error:
                    problems.append(error.detail)
                except OSError as error:
                    problems.append(f"could not audit fixture root `{self._root}`: {error}")
            try:
                shutil.rmtree(self._root)
            except OSError as error:
                problems.append(f"could not remove fixture root `{self._root}`: {error}")
            else:
                self._root_created = False
        return problems

    def _signal_group(self, process, signal_number):
        # Signal only while the leader is unreaped, so its process-group id cannot have been reused.
        if process.returncode is None:
            try:
                os.killpg(process.pid, signal_number)
            except ProcessLookupError:
                pass

    def _wait(self, process, timeout):
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return None

    def _kill_initdb(self):
        process = self._initdb
        if process.poll() is not None:
            return []
        self._signal_group(process, signal.SIGKILL)
        if self._wait(process, self._timeout) is None:
            return [f"initdb process {process.pid} was not reaped after SIGKILL"]
        # initdb's bootstrap backends share its process group; wait for all of them to be gone.
        if not self._await_gone(lambda: os.killpg(process.pid, 0), self._timeout):
            return [f"initdb process group {process.pid} survived SIGKILL"]
        return []

    def _stop_server(self):
        process = self._server
        status = process.poll()
        if status is not None:
            return [f"PostgreSQL server had already exited with status {status}: {self._log_tail('postgres.log')}"]
        # Fast shutdown: the postmaster terminates its sessions and exits only after all its children have.
        self._signal_group(process, signal.SIGINT)
        status = self._wait(process, self._timeout * 2 / 3)
        if status is not None:
            if status != 0:
                return [f"PostgreSQL fast shutdown exited with status {status}: {self._log_tail('postgres.log')}"]
            return []
        problems = [f"PostgreSQL did not complete fast shutdown within {self._timeout_ms * 2 // 3} ms"]
        # Immediate shutdown: the postmaster quits its children and still reaps them before exiting.
        self._signal_group(process, signal.SIGQUIT)
        if self._wait(process, self._timeout / 3) is not None:
            return problems
        # Never signal /proc-discovered PIDs: they may be reused between discovery
        # and signalling. On this failure path the outer sandbox owns cgroup-wide
        # descendant termination; cleanup failure prevents certification.
        self._signal_group(process, signal.SIGKILL)
        if self._wait(process, self._timeout) is None:
            problems.append(f"PostgreSQL server {process.pid} was not reaped after SIGKILL")
        return problems

    def _await_gone(self, probe, timeout):
        deadline = time.monotonic() + timeout
        while True:
            try:
                probe()
            except ProcessLookupError:
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.005)

