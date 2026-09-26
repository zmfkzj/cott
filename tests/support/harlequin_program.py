"""External isolated-process regression of deployed Harlequin's headless CLI."""
import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

KIND = "external_program_regression"
CHECKS = (
    "hsql.sqlite_csv", "hsql.duckdb_csv", "hsql.stdin_sql",
    "hsql.error_statuses", "hsql.machine_spec",
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

def expect_success(result):
    if result.returncode:
        stderr = result.stderr.decode(errors="replace")[-480:]
        raise Failure("exit_status", 0, (result.returncode, stderr))


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
    def __init__(self, app, work):
        self.app, self.work = app, work
        self.number = 0

    def directory(self):
        self.number += 1
        path = self.work / str(self.number)
        path.mkdir()
        return path

    def cli(self, cwd, *args, input=b""):
        return subprocess.run([sys.executable, str(self.app), *map(str, args)], cwd=cwd,
                              env=dict(os.environ), input=input, capture_output=True, timeout=60, check=False)

    def sqlite_csv(self):
        work = self.directory()
        database = work / "data.db"
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE samples (id INTEGER, name TEXT)")
            connection.execute("INSERT INTO samples VALUES (7, 'Ada')")
            connection.execute("INSERT INTO samples VALUES (8, 'comma,name')")
        result = self.cli(work, "--adapter", "sqlite", database, "--csv",
                          "--command", "SELECT id, name FROM samples ORDER BY id")
        expect_success(result)
        expect(result.stdout, b'id,name\n7,Ada\n8,"comma,name"\n', "stdout_mismatch")
        expect(result.stderr, b"", "stderr_mismatch")

    def duckdb_csv(self):
        import duckdb
        work = self.directory()
        database = work / "data.duckdb"
        with duckdb.connect(str(database)) as connection:
            connection.execute("CREATE TABLE samples AS SELECT 17 AS n")
        result = self.cli(work, "--adapter", "duckdb", database, "--csv",
                          "--command", "SELECT n FROM samples")
        expect_success(result)
        expect(result.stdout, b"n\n17\n", "stdout_mismatch")
        expect(result.stderr, b"", "stderr_mismatch")

    def stdin_sql(self):
        work = self.directory()
        result = self.cli(work, "--adapter", "sqlite", ":memory:", "--csv", "--file", "-",
                          input=b"SELECT 42 AS answer;")
        expect_success(result)
        expect(result.stdout, b"answer\n42\n", "stdout_mismatch")

    def error_statuses(self):
        work = self.directory()
        invalid = self.cli(work, "--bad-option")
        expect(invalid.returncode, 2, "argument_exit_status")
        expect(invalid.stdout, b"", "argument_stdout")
        query = self.cli(work, "--adapter", "sqlite", ":memory:",
                         "--command", "SELECT * FROM missing_table")
        expect(query.returncode, 1, "query_exit_status")
        expect(query.stdout, b"", "query_stdout")

    def machine_spec(self):
        work = self.directory()
        info = self.cli(work, "--info")
        expect(info.returncode, 0, "info_exit_status")
        info_json = json.loads(info.stdout)
        expect(info_json["version"], "0.1.0", "info_version")
        if "sqlite" not in info_json["adapters"] or "duckdb" not in info_json["adapters"]:
            raise Failure("info_adapters", "sqlite and duckdb", info_json["adapters"])
        expect(info_json["adapters"]["sqlite"]["read_only"], True, "sqlite_read_only")
        expect(info_json["adapters"]["odbc"]["read_only"], False, "odbc_read_only")
        spec = self.cli(work, "--spec")
        expect(spec.returncode, 0, "spec_exit_status")
        schema = json.loads(spec.stdout)
        if "hsql" not in schema or "sqlite" not in schema["adapters"]:
            raise Failure("spec_adapters", "hsql and sqlite", schema)


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
            report["subject_description"] = "cott deploy output of a verified Harlequin project"
            certified(args.python_root)
        else:
            raise Refusal("unknown subject")
        program = Program(args.app, args.work)
        methods = (program.sqlite_csv, program.duckdb_csv, program.stdin_sql,
                   program.error_statuses, program.machine_spec)
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
