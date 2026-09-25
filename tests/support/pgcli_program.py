"""External regression of deployed pgcli against an isolated scratch PostgreSQL server."""
import argparse
import csv
import io
import json
import os
import pwd
import subprocess
import sys
import threading
import time
from pathlib import Path

KIND = "external_program_regression"
CHECKS = ("database.connect", "database.query_transactions", "database.catalog_refresh",
          "database.import_export", "database.notifications", "cli.run_exit_codes", "cli.interactive")


class Refusal(Exception):
    pass


class Failure(Exception):
    def __init__(self, reason, expected, actual):
        self.reason = reason
        self.detail = f"expected {expected!r}, got {actual!r}"[:600]


def expect(actual, expected, reason):
    if actual != expected:
        raise Failure(reason, expected, actual)


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
                                             "-p", self.port, "-c", "listen_addresses=", "-c", "unix_socket_permissions=0700", "-c", "fsync=off"],
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

    def connect(self):
        import psycopg
        return psycopg.connect(host=str(self.socket), port=self.port, user=self.user, dbname=self.database)


class Program:
    def __init__(self, root, app, work, server):
        from cott_runtime import Nothing, CottList, Ok, Err
        import real.pgcli as api
        self.root, self.app, self.work, self.server = root, app, work, server
        self.api, self.Nothing, self.List, self.Ok, self.Err = api, Nothing, CottList, Ok, Err
        settings = api.ConnectionSettings(host=str(server.socket), port=server.port, user=server.user, password="", database=server.database)
        self.plan = api.ConnectionPlan(settings=settings, dsn="", tls=api.TlsSettings(mode=api.TlsMode_Default(), root_certificate=Nothing(), client=Nothing()), ssh=Nothing())

    def ok(self, value):
        if type(value) is not self.Ok:
            raise Failure("unexpected_error", "Ok", repr(value)[:300])
        return value.value

    def query(self, text, mode=None):
        api = self.api
        request = api.QueryRequest(connection=self.plan, sql=text, max_rows=100,
                                   transaction=mode or api.TransactionMode_AutoCommit(), timing=False)
        return self.api.execute_planned_query(request)

    def connect(self):
        receipt = self.ok(self.api.connect(self.plan))
        expect((receipt.database, receipt.user), (self.server.database, self.server.user), "connection_receipt")
        if not receipt.server_version.startswith("16."):
            raise Failure("server_version", "16.x", receipt.server_version)

    def query_transactions(self):
        api = self.api
        self.ok(self.query("CREATE TABLE cott_regression (n INTEGER)"))
        self.ok(self.query("INSERT INTO cott_regression VALUES (3)", api.TransactionMode_Manual()))
        committed = self.ok(self.query("SELECT n FROM cott_regression"))
        expect((tuple(committed.result.columns), tuple(tuple(row) for row in committed.result.rows)),
               (("n",), (("3",),)), "server_rows")
        denied = self.query("INSERT INTO cott_regression VALUES (4)", api.TransactionMode_ReadOnly())
        if type(denied) is not self.Err or type(denied.error).__name__ != "ClientError_QueryFailed":
            raise Failure("readonly_error", "QueryFailed", repr(denied))
        persisted = self.ok(self.query("SELECT COUNT(*) FROM cott_regression"))
        expect(tuple(row[0] for row in persisted.result.rows), ("1",), "readonly_rollback")

    def catalog_refresh(self):
        api = self.api
        catalog = self.ok(api.refresh_catalog(api.CatalogRefreshRequest(connection=self.plan, include_system=False, limit=100)))
        relations = {(r.schema, r.name, r.kind, tuple(c.name for c in r.columns)) for r in catalog.relations}
        if ("public", "cott_regression", "table", ("n",)) not in relations:
            raise Failure("catalog_missing", "public.cott_regression(n)", relations)
        expect(catalog.limit, 100, "catalog_limit")

    def import_export(self):
        api = self.api
        source = self.work / "input.csv"
        source.write_text('n\n11\n12\n', encoding="utf-8")
        result = self.ok(api.import_delimited(self.plan, api.ImportRequest(table="cott_regression", source=source, delimiter=",", header=True, null_text="", max_rows=2)))
        expect((result.rows, result.path), (2, source), "import_receipt")
        oversized = api.import_delimited(self.plan, api.ImportRequest(table="cott_regression", source=source, delimiter=",", header=True, null_text="", max_rows=1))
        if type(oversized) is not self.Err or type(oversized.error).__name__ != "ClientError_ImportFailed":
            raise Failure("import_limit", "ImportFailed", repr(oversized))
        count = self.ok(self.query("SELECT COUNT(*) FROM cott_regression"))
        expect(count.result.rows[0][0], "3", "import_atomicity")
        target = self.work / "export.csv"
        target.write_bytes(b"old content\n")
        request = lambda limit: api.ExportRequest(sql="SELECT n FROM cott_regression ORDER BY n", target=target, format=api.TableFormat_Csv(), delimiter=",", header=True, max_rows=limit)
        refused = api.export_query(self.plan, request(1))
        if type(refused) is not self.Err or type(refused.error).__name__ != "ClientError_ExportFailed":
            raise Failure("export_limit", "ExportFailed", repr(refused))
        expect(target.read_bytes(), b"old content\n", "export_atomicity")
        receipt = self.ok(api.export_query(self.plan, request(3)))
        expect((receipt.rows, receipt.path), (3, target), "export_receipt")
        expect(list(csv.reader(io.StringIO(target.read_text()))), [["n"], ["3"], ["11"], ["12"]], "export_content")

    def notifications(self):
        api = self.api
        sender_errors = []
        def send():
            try:
                with self.server.connect() as connection:
                    for _ in range(20):
                        time.sleep(0.05)
                        connection.execute("SELECT pg_notify('cott_test', 'hello')")
            except Exception as error:
                sender_errors.append(repr(error))
        thread = threading.Thread(target=send)
        thread.start()
        try:
            result = self.ok(api.receive_notifications(api.NotificationRequest(connection=self.plan,
                              channels=self.List(values=["cott_test"]), timeout_ms=2000, max_notifications=1)))
        finally:
            thread.join(timeout=5)
        expect(sender_errors, [], "notification_sender")
        expect(tuple((n.channel, n.payload) for n in result), (("cott_test", "hello"),), "notification_delivery")
        if result[0].pid <= 0:
            raise Failure("notification_pid", "positive PID", result[0].pid)

    def cli(self, *args, input=b""):
        env = dict(os.environ, PGHOST=str(self.server.socket), PGPORT=self.server.port,
                   PGUSER=self.server.user, PGDATABASE=self.server.database)
        return subprocess.run([sys.executable, str(self.app), *args], cwd=self.work, env=env,
                              input=input, capture_output=True, timeout=60, check=False)

    def run_exit_codes(self):
        help_result = self.cli("--help")
        expect(help_result.returncode, 0, "help_status")
        if b"--command" not in help_result.stdout:
            raise Failure("usage_text", b"--command", help_result.stdout[:500])
        invalid = self.cli("--unknown-option")
        expect(invalid.returncode, 2, "invalid_status")
        successful = self.cli("-c", "SELECT 8 AS answer")
        expect(successful.returncode, 0, "sql_status")
        if b"answer" not in successful.stdout or b"8" not in successful.stdout:
            raise Failure("sql_output", "server row 8", successful.stdout[:500])
        failed = self.cli("-c", "SELECT * FROM no_such_regression_table")
        expect(failed.returncode, 1, "query_error_status")

    def interactive(self):
        result = self.cli(input=b"SELECT 9 AS nine;\n\\refresh\n\\q\n")
        expect(result.returncode, 0, "interactive_status")
        if b"nine" not in result.stdout or b"9" not in result.stdout or b"Catalog refreshed:" not in result.stdout:
            raise Failure("interactive_output", "SQL row and catalog refresh", result.stdout[:600])


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
            for name, method in zip(CHECKS, (program.connect, program.query_transactions, program.catalog_refresh,
                                            program.import_export, program.notifications, program.run_exit_codes,
                                            program.interactive)):
                try:
                    method()
                    report["checks"].append(dict(id=name, passed=True, reason=None, detail=""))
                except Failure as error:
                    report["checks"].append(dict(id=name, passed=False, reason=error.reason, detail=error.detail))
                except Exception as error:
                    report["checks"].append(dict(id=name, passed=False, reason="exception", detail=f"{type(error).__name__}: {error}"[:600]))
    except Refusal as error:
        report["refusal"] = str(error)
        print(json.dumps(report, sort_keys=True), flush=True)
        return 2
    report["verdict"] = "passed" if all(c["passed"] for c in report["checks"]) else "failed"
    print(json.dumps(report, sort_keys=True), flush=True)
    return 0 if report["verdict"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
