"""External isolated-process regression of the deployed Harlequin CLI and live session."""
import argparse
import contextlib
import io
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

KIND = "external_program_regression"
CHECKS = (
    "cli.batch_sqlite_format", "cli.interactive_sqlite", "cli.exit_statuses",
    "run.disconnect_rolls_back", "cli.batch_duckdb_format",
)


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


class Program:
    def __init__(self, root, app, work):
        self.root, self.app, self.work = root, app, work
        self.number = 0

    def directory(self):
        self.number += 1
        path = self.work / str(self.number)
        path.mkdir()
        return path

    def cli(self, cwd, *args, input=b""):
        return subprocess.run([sys.executable, str(self.app), "--no-config", *map(str, args)], cwd=cwd,
                              env=dict(os.environ), input=input, capture_output=True, timeout=60, check=False)

    def batch_sqlite_format(self):
        work = self.directory()
        database = work / "data.db"
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE samples (id INTEGER, name TEXT, raw BLOB)")
            connection.execute("INSERT INTO samples VALUES (7, 'line\tbreak', x'00FF')")
        query = work / "query.sql"
        query.write_text("SELECT id, name, raw FROM samples;\n", encoding="utf-8")
        result = self.cli(work, "--adapter", "sqlite", "--query-file", query, database)
        expect(result.returncode, 0, "exit_status")
        expect(result.stdout, b"id\tname\traw\n7\tline\\tbreak\t0x00ff\n", "stdout_mismatch")
        expect(result.stderr, b"", "stderr_mismatch")

    def interactive_sqlite(self):
        work = self.directory()
        result = self.cli(work, "--adapter", "sqlite", ":memory:", input=b"CREATE TABLE t (v INTEGER);\nINSERT INTO t VALUES (42);\nSELECT v FROM t;\n.quit\n")
        expect(result.returncode, 0, "exit_status")
        expect(result.stdout, b"sql> OK\nsql> OK, 1 rows affected\nsql> v\n42\nsql> ", "stdout_mismatch")
        expect(result.stderr, b"", "stderr_mismatch")

    def exit_statuses(self):
        work = self.directory()
        invalid = self.cli(work, "--bad-option")
        expect(invalid.returncode, 2, "argument_exit_status")
        expect(invalid.stdout, b"", "argument_stdout")
        missing = self.cli(work, "--adapter", "sqlite", "--query-file", work / "missing.sql", ":memory:")
        expect(missing.returncode, 1, "batch_exit_status")
        expect(missing.stdout, b"", "batch_stdout")
        failed = self.cli(work, "--adapter", "sqlite", work / "missing-dir" / "db.sqlite")
        expect(failed.returncode, 1, "connection_exit_status")
        for result in (invalid, missing, failed):
            if not result.stderr.startswith(b"harlequin: "):
                raise Failure("error_prefix", b"harlequin: ...", result.stderr)

    def disconnect_rolls_back(self):
        from cott_runtime import CottList, Err, Ok
        import real.harlequin.core as api

        work = self.directory()
        database = work / "rollback.db"
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE t (value INTEGER)")
        query = work / "insert.sql"
        query.write_text("INSERT INTO t VALUES (19)", encoding="utf-8")
        genuine_connect, genuine_disconnect = api.connect, api.disconnect
        opened, closed = [], []

        def connect(request):
            result = genuine_connect(request)
            if type(result) is Ok:
                opened.append(result.value)
                lease = api.begin_transaction(result.value)
                if type(lease) is not Ok:
                    raise Failure("lease_begin", "Ok", repr(lease))
            return result

        def disconnect(connection):
            closed.append(connection)
            return genuine_disconnect(connection)

        api.connect, api.disconnect = connect, disconnect
        stdout, stderr = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    api.run(CottList(values=["--no-config", "--adapter", "sqlite",
                                              "--query-file", str(query), str(database)]))
                except SystemExit as error:
                    status = error.code
                else:
                    raise Failure("missing_exit", "SystemExit(0)", "ordinary return")
        finally:
            api.connect, api.disconnect = genuine_connect, genuine_disconnect
        expect(status, 0, "exit_status")
        expect(len(opened), 1, "connect_count")
        expect(closed, opened, "disconnect_count")
        with sqlite3.connect(database) as connection:
            expect(connection.execute("SELECT value FROM t").fetchall(), [], "uncommitted_rollback")
        if type(api.execute_statements(opened[0], "SELECT 1", 1)) is not Err:
            raise Failure("closed_session", "Err on disconnected session", "live session")

    def batch_duckdb_format(self):
        import duckdb
        work = self.directory()
        database = work / "data.duckdb"
        with duckdb.connect(str(database)) as connection:
            connection.execute("CREATE TABLE t AS SELECT 17 AS n")
        query = work / "query.sql"
        query.write_text("SELECT n FROM t;", encoding="utf-8")
        result = self.cli(work, "--adapter", "duckdb", "--query-file", query, database)
        expect(result.returncode, 0, "exit_status")
        expect(result.stdout, b"n\n17\n", "stdout_mismatch")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-root", required=True, type=Path)
    parser.add_argument("--app", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--subject", required=True)
    args = parser.parse_args()
    report = dict(evidence_kind=KIND, cott_scenario_evidence=False, subject=args.subject,
                  subject_description=None, verdict="refused", refusal=None, checks=[])
    try:
        if args.subject == "verified-deployment":
            report["subject_description"] = "cott deploy output of verified examples/real/harlequin"
            certified(args.python_root)
        elif args.subject.startswith("defect-fixture:"):
            report["subject_description"] = "compiler-bound defect in a throwaway copy; never certified"
        else:
            raise Refusal("unknown subject")
        sys.path.insert(0, str(args.python_root))
        import real.harlequin.core  # noqa: F401; require public facade import
        program = Program(args.python_root, args.app, args.work)
        methods = (program.batch_sqlite_format, program.interactive_sqlite, program.exit_statuses,
                   program.disconnect_rolls_back, program.batch_duckdb_format)
        for name, method in zip(CHECKS, methods):
            try:
                method()
                report["checks"].append(dict(id=name, passed=True, reason=None, detail=""))
            except Failure as failure:
                report["checks"].append(dict(id=name, passed=False, reason=failure.reason, detail=failure.detail))
            except Exception as error:
                report["checks"].append(dict(id=name, passed=False, reason="exception", detail=f"{type(error).__name__}: {error}"[:600]))
    except Refusal as error:
        report["refusal"] = str(error)
        print(json.dumps(report, sort_keys=True), flush=True)
        return 2
    report["verdict"] = "passed" if all(check["passed"] for check in report["checks"]) else "failed"
    print(json.dumps(report, sort_keys=True), flush=True)
    return 0 if report["verdict"] == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
