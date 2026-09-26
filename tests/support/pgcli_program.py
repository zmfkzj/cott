"""External regression of deployed pgcli against an isolated scratch PostgreSQL server.

Expected texts are those of upstream pgcli 4.7.1 run against the same kind of server. The server listens on
its Unix socket and on 127.0.0.1 inside the sandbox's private network namespace; the SSH check starts the
host's own OpenSSH sshd, unprivileged, on that private loopback.
"""
import argparse
import datetime
import json
import os
import pty
import pwd
import re
import select
import signal
import struct
import subprocess
import sys
import termios
import fcntl
import time
from pathlib import Path

KIND = "external_program_regression"
CHECKS = ("database.connect", "database.transactions", "database.completion_metadata", "cli.special_commands",
          "database.notifications", "cli.run_exit_codes", "cli.interactive", "cli.pty_interactive", "cli.watch",
          "cli.external_editor", "cli.pager", "cli.keyring_without_backend", "database.ssh_tunnel")
ANSI = re.compile(rb"\x1b\[[0-9;?]*[a-zA-Z]")
KEYRING_MISSING = (
    "Load your password from keyring returned:\nNo recommended backend was available. Install a recommended 3rd party "
    "backend package; or, install the keyrings.alt package if you want to use the non-recommended backends. See "
    "https://pypi.org/project/keyring for details.\nTo remove this message do one of the following:\n- prepare keyring as "
    "described at: https://keyring.readthedocs.io/en/stable/\n- uninstall keyring: pip uninstall keyring\n- disable keyring "
    "in our configuration: add keyring = False to [main]\n")


class Refusal(Exception):
    pass


class Failure(Exception):
    def __init__(self, reason, expected, actual):
        self.reason = reason
        self.detail = f"expected {expected!r}, got {actual!r}"[:900]


def expect(actual, expected, reason):
    if actual != expected:
        raise Failure(reason, expected, actual)


def expect_in(needle, haystack, reason):
    if needle not in haystack:
        raise Failure(reason, needle, haystack[-900:])


def certified(root):
    try:
        record = json.loads((root.parent / "generation.json").read_text())
        current = record["current"]
        snapshot = record["snapshots"][current]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise Refusal(f"unreadable generation record: {error}") from error
    if snapshot.get("verified") is not True or record.get("last_verified") != current or snapshot.get("unresolved"):
        raise Refusal("generation record is not a resolved verified current snapshot")


class Server:
    def __init__(self, binary, work):
        self.binary, self.work = binary, work
        self.socket = work / "socket"
        self.data = work / "cluster"
        self.user = pwd.getpwuid(os.getuid()).pw_name
        self.database = "postgres"
        self.port = "55433"
        self.process = None

    def __enter__(self):
        self.socket.mkdir()
        self.socket.chmod(0o700)
        share = self.binary.parent.parent.parent.parent / "share/postgresql/16"
        # A relocated Ubuntu package has usr/lib/postgresql/16/bin and usr/share/postgresql/16.
        if not share.is_dir():
            raise Refusal(f"PostgreSQL initdb share directory missing: {share}")
        initdb = subprocess.run([str(self.binary / "initdb"), "-D", str(self.data), "-L", str(share), "-A", "trust", "--no-instructions"],
                                capture_output=True, timeout=45, check=False)
        if initdb.returncode:
            raise Refusal(f"initdb failed: {initdb.stderr[-500:]!r}")
        log = (self.work / "postgres.log").open("wb")
        try:
            self.process = subprocess.Popen([str(self.binary / "postgres"), "-D", str(self.data), "-k", str(self.socket),
                                             "-p", self.port, "-c", "listen_addresses=127.0.0.1", "-c", "unix_socket_permissions=0700", "-c", "fsync=off"],
                                            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        finally:
            log.close()
        import psycopg
        for _ in range(100):
            if self.process.poll() is not None:
                raise Refusal(f"PostgreSQL exited early: {(self.work / 'postgres.log').read_text()[-500:]}")
            try:
                with psycopg.connect(host=str(self.socket), port=self.port, user=self.user, dbname=self.database, connect_timeout=1):
                    return self
            except psycopg.OperationalError:
                time.sleep(0.1)
        raise Refusal(f"PostgreSQL did not become ready: {(self.work / 'postgres.log').read_text()[-500:]}")

    def __exit__(self, *_):
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)

    def execute(self, sql):
        import psycopg
        with psycopg.connect(host=str(self.socket), port=self.port, user=self.user, dbname=self.database, autocommit=True) as connection:
            cursor = connection.execute(sql)
            return cursor.fetchall() if sql.lstrip().upper().startswith("SELECT") else None


class Terminal:
    """A program on a pseudo-terminal; expectations match the screen bytes with ANSI control sequences removed."""

    def __init__(self, argv, environment, cwd, rows=24, columns=100):
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.chdir(cwd)
            os.execve(argv[0], argv, environment)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, columns, 0, 0))
        self.screen = bytearray()
        self.mark = 0

    def text(self):
        return ANSI.sub(b"", bytes(self.screen))

    def expect(self, needle, timeout=20.0):
        """Wait for needle after the previous match and return the text between the two matches."""
        deadline = time.monotonic() + timeout
        while True:
            text = self.text()
            found = text.find(needle, self.mark)
            if found >= 0:
                seen, self.mark = text[self.mark:found], found + len(needle)
                return seen.decode("utf-8", "replace")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise Failure("pty_screen", needle.decode(), text[-900:].decode("utf-8", "replace"))
            ready, _, _ = select.select([self.fd], [], [], remaining)
            if ready:
                try:
                    chunk = os.read(self.fd, 65536)
                except OSError:
                    chunk = b""
                if not chunk:
                    raise Failure("pty_closed", needle.decode(), text[-900:].decode("utf-8", "replace"))
                self.screen.extend(chunk)
                if b"\x1b[6n" in chunk:
                    os.write(self.fd, b"\x1b[1;1R")

    def send(self, data):
        os.write(self.fd, data)

    def close(self):
        try:
            os.kill(self.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            os.waitpid(self.pid, 0)
        except ChildProcessError:
            pass
        os.close(self.fd)


class Program:
    def __init__(self, root, app, work, server):
        from cott_runtime import Nothing, CottList, Ok
        import real.pgcli.connection as connection
        import real.pgcli.completion as completion
        self.root, self.app, self.work, self.server = root, app, work, server
        self.connection, self.completion = connection, completion
        self.Nothing, self.List, self.Ok = Nothing, CottList, Ok
        self.config = work / ".config/pgcli/config"

    def ok(self, value, reason="unexpected_error"):
        if type(value) is not self.Ok:
            raise Failure(reason, "Ok", repr(value)[:300])
        return value.value

    def open_request(self, database="postgres"):
        c = self.connection
        spec = c.ConnectionSpec(database=database, host=str(self.server.socket), user=self.server.user, port=self.server.port,
                                password="", dsn="", extra=self.List(values=()))
        return c.OpenRequest(spec=spec, application_name="pgcli", force_password_prompt=False, never_password_prompt=True,
                             keyring_enabled=False, explicit_timeout=self.Nothing(), default_timeout=30, pgpassword="",
                             pgconnect_timeout="", dsn_alias=self.Nothing(), explicit_tunnel=self.Nothing(),
                             dsn_tunnels=self.List(values=()), host_tunnels=self.List(values=()))

    def cli(self, *args, input=b"", env=None):
        environment = dict(os.environ, PGHOST=str(self.server.socket), PGPORT=self.server.port,
                           PGUSER=self.server.user, PGDATABASE=self.server.database, COLUMNS="80", LINES="24")
        environment.pop("PAGER", None)
        environment.update(env or {})
        result = subprocess.run([sys.executable, str(self.app), *args], cwd=self.work, env=environment,
                                input=input, capture_output=True, timeout=90, check=False)
        return result.returncode, result.stdout.decode("utf-8", "replace"), result.stderr.decode("utf-8", "replace")

    def connect(self):
        c = self.connection
        executor = self.ok(c.open_executor(self.open_request()), "open_executor")
        expect((executor.dbname, executor.user, executor.host, executor.port), (self.server.database, self.server.user,
                                                                               str(self.server.socket), self.server.port), "executor_identity")
        if not executor.server_version.startswith("16.") or executor.pid <= 0 or not executor.superuser:
            raise Failure("executor_facts", "16.x, pid > 0, superuser", (executor.server_version, executor.pid, executor.superuser))
        expect(type(c.executor_transaction_status(executor)).__name__, "TransactionStatus_Idle", "idle_status")
        self.server.execute("CREATE DATABASE cott_other")
        moved = self.ok(c.reconnect_executor(executor, c.ReconnectRequest(database="cott_other", user="", host="", port="")), "reconnect")
        expect(moved.dbname, "cott_other", "reconnect_database")
        refused = c.reconnect_executor(moved, c.ReconnectRequest(database="cott_missing_db", user="", host="", port=""))
        if type(refused) is self.Ok:
            raise Failure("reconnect_failure", "Err", repr(refused)[:200])
        path = self.ok(c.read_search_path(moved), "previous_connection_kept")
        if "public" not in list(path):
            raise Failure("search_path", "public", list(path))
        copied = self.ok(c.copy_executor(moved), "copy_executor")
        if copied.pid == moved.pid or copied.dbname != "cott_other":
            raise Failure("copy_executor", "independent session on cott_other", (copied.pid, moved.pid, copied.dbname))
        c.close_executor(copied)
        c.close_executor(moved)

    def transactions(self):
        status, out, err = self.cli("-c", "CREATE TABLE cott_regression (n INTEGER)")
        expect(status, 0, "ddl_status")
        expect_in("CREATE TABLE\nTime: ", out, "ddl_output")
        status, out, err = self.cli("-c", "BEGIN", "-c", "INSERT INTO cott_regression VALUES (3)", "-c", "COMMIT")
        expect_in("INSERT 0 1", out, "insert_output")
        status, out, err = self.cli("-c", "BEGIN; INSERT INTO cott_regression VALUES (4); ROLLBACK;")
        status, out, err = self.cli("-t", "-c", "SELECT n FROM cott_regression")
        expect(out, "3\n", "tuples_only_rows")
        status, out, err = self.cli("-c", "select boom_not_a_column; select 444")
        expect(status, 0, "error_status")
        expect_in('column "boom_not_a_column" does not exist', out, "error_text")
        if "444" in out:
            raise Failure("on_error_stop", "no 444", out)
        status, out, err = self.cli("--row-limit", "2", "-c", "select generate_series(1,5)")
        expect_in("The result was limited to 2 rows", out, "row_limit_notice")
        expect_in("+-----------------+\n| generate_series |\n|-----------------|\n| 1               |\n| 2               |\n+-----------------+\nSELECT 2\n", out, "row_limit_table")

    def completion_metadata(self):
        c, m = self.connection, self.completion
        executor = self.ok(c.open_executor(self.open_request()), "open_executor")
        catalog = self.ok(m.refresh_completion_metadata(executor, m.MetadataRefreshRequest(casing_file=self.Nothing(), generate_casing_file=False)), "refresh")
        metadata = catalog.unwrap()
        tables = {(schema, name, tuple(column[0] for column in columns)) for schema, name, columns in metadata["tables"]}
        if ("public", "cott_regression", ("n",)) not in tables:
            raise Failure("catalog_missing", "public.cott_regression(n)", sorted(tables)[:20])
        if "postgres" not in metadata["databases"] or "public" not in metadata["search_path"]:
            raise Failure("catalog_lists", "postgres database and public schema", (metadata["databases"], metadata["search_path"]))
        if not any(function[1] == "now" for function in metadata["functions"]):
            raise Failure("catalog_functions", "now()", len(metadata["functions"]))
        c.close_executor(executor)

    def special_commands(self):
        status, out, err = self.cli("-c", "\\dt")
        expect_in("| public | cott_regression | table |", out, "list_tables")
        status, out, err = self.cli("-c", "\\T csv", "-c", "select n from cott_regression")
        expect_in('Changed table format to csv\nTime: ', out, "table_format_message")
        expect_in('"n"\n"3"\nSELECT 1\n', out, "csv_output")
        status, out, err = self.cli("-c", "\\conninfo")
        expect_in(f'You are connected to database "postgres" as user "{self.server.user}" on socket "{self.server.socket}" at port "{self.server.port}".', out, "conninfo")
        status, out, err = self.cli("-c", "\\echo hola")
        expect_in("hola\n", out, "echo")
        script = self.work / "script.sql"
        script.write_text("SELECT 77 AS seventy;\n", encoding="utf-8")
        status, out, err = self.cli("-c", f"\\i {script}")
        expect_in("| seventy |", out, "include_file")
        target = self.work / "out.txt"
        status, out, err = self.cli("-c", f"\\o {target}", "-c", "select 5 as five")
        expect_in(f'Writing to file "{target}"', out, "output_file_message")
        expect_in("select 5 as five\n+------+\n| five |\n", target.read_text(encoding="utf-8"), "output_file_content")
        log = self.work / "session.log"
        status, out, err = self.cli("--log-file", str(log), "-c", "\\qecho hi")
        lines = log.read_text(encoding="utf-8").splitlines()
        if len(lines) < 3 or lines[1:3] != ["\\qecho hi", "hi"]:
            raise Failure("log_file", ["<iso time>", "\\qecho hi", "hi"], lines)
        datetime.datetime.fromisoformat(lines[0].strip())
        status, out, err = self.cli("-c", "\\ns cnt SELECT count(*) FROM cott_regression")
        expect_in("Saved.", out, "named_save")
        expect_in("cnt = SELECT count(*) FROM cott_regression", self.config.read_text(encoding="utf-8"), "named_persisted")
        status, out, err = self.cli("-c", "\\n cnt")
        expect_in("> SELECT count(*) FROM cott_regression\n+-------+\n| count |\n|-------|\n| 1     |\n+-------+\nSELECT 1\n", out, "named_run")
        status, out, err = self.cli("-c", "\\nd cnt")
        expect_in("cnt: Deleted", out, "named_delete")
        copy_target = self.work / "copy.csv"
        status, out, err = self.cli("-c", f"\\copy cott_regression to '{copy_target}' with csv")
        expect(copy_target.read_text(encoding="utf-8") if copy_target.exists() else None, "3\n", "copy_to_file")
        status, out, err = self.cli("-c", "\\x on", "-c", "select 1 as a")
        expect_in("Expanded display is on.", out, "expanded_toggle")
        expect_in("-[ RECORD 1 ]-------------------------\na | 1\n", out, "expanded_output")

    def notifications(self):
        status, out, err = self.cli("-c", "LISTEN cott_chan", "-c", "NOTIFY cott_chan, 'hello'")
        if not re.search(r'Notification received on channel "cott_chan" \(PID \d+\):\nhello\n', out):
            raise Failure("notification_delivery", "notification line", out)

    def run_exit_codes(self):
        status, out, err = self.cli("--help")
        expect(status, 0, "help_status")
        if not out.startswith("Usage: pgcli [OPTIONS] [DBNAME] [USERNAME]\n") or "-c, --command TEXT" not in out:
            raise Failure("usage_text", "click help text", out[:500])
        status, out, err = self.cli("--version")
        expect((status, out), (0, "Version: 4.7.1\n"), "version")
        status, out, err = self.cli("--bogus")
        expect((status, err), (2, "Usage: pgcli [OPTIONS] [DBNAME] [USERNAME]\nTry 'pgcli --help' for help.\n\nError: No such option '--bogus'. (Did you mean one of: '--host', '--user'?)\n"), "usage_error")
        status, out, err = self.cli("-p", "x")
        expect((status, err), (2, "Usage: pgcli [OPTIONS] [DBNAME] [USERNAME]\nTry 'pgcli --help' for help.\n\nError: Invalid value for '-p' / '--port': 'x' is not a valid integer.\n"), "bad_port")
        status, out, err = self.cli("--ping")
        expect((status, out), (0, "PONG\n"), "ping")
        status, out, err = self.cli("-l")
        expect(status, 0, "list_status")
        expect_in("List of databases\n+", out, "list_output")
        status, out, err = self.cli("-c", "SELECT 8 AS answer")
        expect(status, 0, "sql_status")
        expect_in("+--------+\n| answer |\n|--------|\n| 8      |\n+--------+\nSELECT 1\nTime: ", out, "sql_output")
        status, out, err = self.cli("-h", str(self.work / "no-socket-here"), "-c", "select 1")
        expect(status, 1, "connect_failure_status")

    def interactive(self):
        status, out, err = self.cli(input=b"SELECT 9 AS nine;\n\\q\n")
        expect(status, 0, "interactive_status")
        for needle in ("Server: PostgreSQL 16.", "Version: 4.7.1\nHome: https://pgcli.com\n", "| nine |", "| 9    |", "Goodbye!"):
            expect_in(needle, out, "interactive_output")
        history = self.work / ".config/pgcli/history"
        expect_in("\n+SELECT 9 AS nine;\n", history.read_text(encoding="utf-8") if history.exists() else "", "history_file")

    def environment(self, **extra):
        environment = dict(os.environ, PGHOST=str(self.server.socket), PGPORT=self.server.port,
                           PGUSER=self.server.user, PGDATABASE=self.server.database, TERM="xterm")
        environment.pop("PAGER", None)
        environment.update(extra)
        return environment

    def terminal(self, **extra):
        return Terminal([sys.executable, str(self.app)], self.environment(**extra), self.work)

    def script(self, name, body):
        """An executable Python helper program, run by the interpreter under test."""
        path = self.work / name
        path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
        path.chmod(0o755)
        return path

    def pty_interactive(self):
        terminal = self.terminal()
        try:
            terminal.expect(b"postgres>")
            terminal.expect(b"[F2] Smart Completion: ON")
            terminal.send(b"\x1bOR")  # F3
            terminal.expect(b"[F3] Multiline: ON")
            terminal.send(b"SELECT n FROM cott_reg")
            terminal.expect(b"cott_regression")
            terminal.send(b"\t")
            terminal.send(b"\r")
            time.sleep(0.5)
            terminal.send(b";\r")
            terminal.expect(b"SELECT 1")
            terminal.send(b"\\q\r")
            terminal.expect(b"Goodbye!")
        finally:
            terminal.close()

    def watch(self):
        terminal = self.terminal()
        try:
            terminal.expect(b"postgres>")
            terminal.send(b"SELECT 42 AS w \\watch 1\r")
            for _ in range(2):
                expect_in("| 42 |", terminal.expect(b"Waiting for 1 seconds before repeating"), "watch_repeat")
            terminal.send(b"\x03")
            terminal.expect(b"postgres>")
            terminal.send(b"\\watch 1\r")  # a bare \watch repeats the last query
            expect_in("| 42 |\n+----+\nSELECT 1\nTime: ", terminal.expect(b"Waiting for 1 seconds before repeating").replace("\r", ""), "watch_last_query")
            terminal.send(b"\x03")
            terminal.expect(b"postgres>")
            terminal.send(b"\\q\r")
            terminal.expect(b"Goodbye!")
        finally:
            terminal.close()

    def external_editor(self):
        self.server.execute("CREATE VIEW cott_view AS SELECT 1 AS one")
        log = self.work / "editor.log"
        editor = self.script("editor.py", "import sys\nfrom pathlib import Path\npath = Path(sys.argv[-1])\n"
                             f"with open({str(log)!r}, 'a', encoding='utf-8') as log:\n"
                             "    log.write('<<' + path.read_text(encoding='utf-8') + '>>' + path.suffix + '\\n')\n"
                             "path.write_text('SELECT 7 AS edited', encoding='utf-8')\n")
        terminal = self.terminal(EDITOR=str(editor))
        try:
            terminal.expect(b"postgres>")
            terminal.send(b"SELECT 42 AS w\r")
            terminal.expect(b"| 42 |")
            for command in (b"\\e\r", b"\\ev cott_view\r"):
                terminal.expect(b"postgres>")
                terminal.send(command)
                terminal.expect(b"postgres> SELECT 7 AS edited")  # the editor's text is the next prompt's default
                time.sleep(0.5)
                terminal.send(b"\r")
                terminal.expect(b"| edited |")
            terminal.expect(b"postgres>")
            terminal.send(b"\\q\r")
            terminal.expect(b"Goodbye!")
        finally:
            terminal.close()
        expect(log.read_text(encoding="utf-8") if log.exists() else None,
               '<<SELECT 42 AS w\n\n# Type your query above this line.\n>>.sql\n'
               '<<CREATE OR REPLACE VIEW "public"."cott_view" AS \n SELECT 1 AS one;\n\n# Type your query above this line.\n>>.sql\n',
               "editor_files")

    def pager(self):
        paged = self.work / "pager.out"
        pager = self.script("pager.py", f"import os, sys\nwith open({str(paged)!r}, 'a', encoding='utf-8') as out:\n"
                            "    out.write('LESS=' + os.environ.get('LESS', '') + '\\n' + sys.stdin.read())\n")
        terminal = self.terminal(PAGER=str(pager))
        try:
            terminal.expect(b"postgres>")
            terminal.send(b"select 1 as short\r")  # fits the 24-row screen: printed directly
            terminal.expect(b"| short |")
            terminal.expect(b"Time: ")
            if paged.exists():
                raise Failure("short_output_paged", "no pager run", paged.read_text(encoding="utf-8"))
            terminal.send(b"select generate_series(1, 60) as g\r")
            screen = terminal.expect(b"Time: ")  # the timing line follows the pager run on the screen
            if "| 60 |" in screen:
                raise Failure("tall_output_on_screen", "rows only in the pager", screen[-300:])
            terminal.send(b"\\q\r")
            terminal.expect(b"Goodbye!")
        finally:
            terminal.close()
        expect(paged.read_text(encoding="utf-8") if paged.exists() else None,
               "LESS=-SRXF\n+----+\n| g  |\n|----|\n" + "".join(f"| {n:<2} |\n" for n in range(1, 61)) + "+----+\nSELECT 60\n",
               "pager_input")

    def keyring_without_backend(self):
        status, out, err = self.cli("-c", "select 1 as k")
        expect((status, err), (0, KEYRING_MISSING), "keyring_message")
        expect_in("| k |", out, "keyring_query_output")
        disabled = self.work / "no-keyring.config"
        disabled.write_text("[main]\nkeyring = False\n", encoding="utf-8")
        status, out, err = self.cli("--pgclirc", str(disabled), "-c", "select 1 as k")
        expect((status, err), (0, ""), "keyring_disabled")

    def ssh_tunnel(self):
        for tool in ("/usr/sbin/sshd", "/usr/bin/ssh-keygen"):
            if not os.access(tool, os.X_OK):
                raise Failure("openssh_missing", tool, "absent")
        keys = self.work / ".ssh"
        keys.mkdir(mode=0o700, exist_ok=True)
        for path in (self.work / "ssh_host_key", keys / "id_ed25519"):
            subprocess.run(["/usr/bin/ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(path)], check=True, capture_output=True, timeout=30)
        (self.work / "authorized_keys").write_bytes((keys / "id_ed25519.pub").read_bytes())
        config = self.work / "sshd_config"
        config.write_text(f"Port 22022\nListenAddress 127.0.0.1\nHostKey {self.work}/ssh_host_key\nPidFile {self.work}/sshd.pid\n"
                          f"AuthorizedKeysFile {self.work}/authorized_keys\nStrictModes no\nUsePAM no\nPasswordAuthentication no\n"
                          "KbdInteractiveAuthentication no\nAllowTcpForwarding yes\nLogLevel DEBUG1\n", encoding="utf-8")
        log = self.work / "sshd.log"
        sshd = subprocess.Popen(["/usr/sbin/sshd", "-D", "-f", str(config), "-E", str(log)], stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            import socket
            for _ in range(100):
                if sshd.poll() is not None:
                    raise Failure("sshd_start", "running sshd", log.read_text(encoding="utf-8")[-500:] if log.exists() else sshd.returncode)
                try:
                    socket.create_connection(("127.0.0.1", 22022), timeout=1).close()
                    break
                except OSError:
                    time.sleep(0.1)
            target = ("-h", "127.0.0.1", "-p", self.server.port, "-U", self.server.user, "-d", self.server.database)
            status, out, err = self.cli("--ssh-tunnel", f"{self.server.user}@127.0.0.1:22022", *target, "-c", "select 'tunnelled' as route")
            expect(status, 0, "tunnel_status")
            expect_in("| route     |\n|-----------|\n| tunnelled |\n+-----------+\nSELECT 1\n", out, "tunnel_output")
            sshd_log = log.read_text(encoding="utf-8")
            expect_in(f"Accepted publickey for {self.server.user} from 127.0.0.1", sshd_log, "tunnel_authenticated")
            if not re.search(rf"server_request_direct_tcpip: originator 127\.0\.0\.1 port \d+, target 127\.0\.0\.1 port {self.server.port}(?!\d)", sshd_log):
                raise Failure("tunnel_forwarded", "direct-tcpip channel to the database port", sshd_log[-600:])
            status, out, err = self.cli("--ssh-tunnel", f"{self.server.user}@127.0.0.1:22023", *target, "-c", "select 1")
            expect(status, 1, "unreachable_gateway_status")
            expect_in("Could not establish session to SSH gateway\n", err, "unreachable_gateway_error")
        finally:
            sshd.terminate()
            try:
                sshd.wait(timeout=5)
            except subprocess.TimeoutExpired:
                sshd.kill()
                sshd.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser()
    for field in ("python-root", "app", "work", "postgres-bin"):
        parser.add_argument("--" + field, required=True, type=Path)
    parser.add_argument("--subject", required=True)
    args = parser.parse_args()
    report = dict(evidence_kind=KIND, cott_scenario_evidence=False, subject=args.subject,
                  subject_description=None, verdict="refused", refusal=None, checks=[])
    try:
        if args.subject == "verified-deployment":
            report["subject_description"] = "cott deploy output of verified examples/real/pgcli"
            certified(args.python_root)
        elif args.subject.startswith("defect-fixture:"):
            report["subject_description"] = "compiler-bound defect in a throwaway copy; never certified"
        else:
            raise Refusal("unknown subject")
        sys.path.insert(0, str(args.python_root))
        with Server(args.postgres_bin, args.work) as server:
            program = Program(args.python_root, args.app, args.work, server)
            for name, method in zip(CHECKS, (program.connect, program.transactions, program.completion_metadata,
                                            program.special_commands, program.notifications, program.run_exit_codes,
                                            program.interactive, program.pty_interactive, program.watch,
                                            program.external_editor, program.pager, program.keyring_without_backend,
                                            program.ssh_tunnel)):
                try:
                    method()
                    report["checks"].append(dict(id=name, passed=True, reason=None, detail=""))
                except Failure as error:
                    report["checks"].append(dict(id=name, passed=False, reason=error.reason, detail=error.detail))
                except Exception as error:
                    report["checks"].append(dict(id=name, passed=False, reason="exception", detail=f"{type(error).__name__}: {error}"[:900]))
    except Refusal as error:
        report["refusal"] = str(error)
        print(json.dumps(report, sort_keys=True), flush=True)
        return 2
    report["verdict"] = "passed" if all(c["passed"] for c in report["checks"]) else "failed"
    print(json.dumps(report, sort_keys=True), flush=True)
    return 0 if report["verdict"] == "passed" else 1


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    sys.exit(main())
