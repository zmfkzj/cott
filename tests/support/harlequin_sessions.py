"""External SQLite/DuckDB retained-session and transaction smoke via public facades."""
import sqlite3
import tempfile
from pathlib import Path

import duckdb
from cott_runtime import CottList, Nothing, Ok, Some
from real.harlequin.adapters import (
    AdapterKind_DuckDb, AdapterKind_Sqlite, ConnectionRequest, close_connection,
    commit_transaction, connect, execute_statements, rollback_transaction,
    run_scalar_query, toggle_transaction_mode,
)
from real.harlequin.history import record_query, recent_queries, update_query
from real.harlequin.history_types import HistoryFilter, QueryRecord, QueryStatus_Error, QueryStatus_Ok


def session(kind, path):
    opened = connect(ConnectionRequest(adapter=kind, conn_str=CottList(values=[str(path)]),
                                       read_only=False, settings=CottList(values=[])))
    assert isinstance(opened, Ok), opened
    return opened.value


def execute(connection, sql):
    statements = execute_statements(connection, CottList(values=[sql]), Nothing(), False)
    assert len(statements) == 1 and isinstance(statements[0].failure, Nothing), statements


def scalar(connection, sql):
    outcome = run_scalar_query(connection, sql)
    assert isinstance(outcome, Ok), outcome
    assert isinstance(outcome.value, Some), outcome
    return outcome.value.value


with tempfile.TemporaryDirectory(prefix="cott-harlequin-sessions-") as directory:
    root = Path(directory)
    sqlite = root / "sqlite.db"
    sqlite3.connect(sqlite).close()
    connection = session(AdapterKind_Sqlite(), sqlite)
    try:
        execute(connection, "CREATE TABLE ledger(value INTEGER)")
        execute(connection, "INSERT INTO ledger VALUES (7)")
        assert scalar(connection, "SELECT COUNT(*) FROM ledger") == "1"
        manual = toggle_transaction_mode(connection)
        assert isinstance(manual, Ok), manual
        connection = manual.value
        execute(connection, "INSERT INTO ledger VALUES (19)")
        assert scalar(connection, "SELECT COUNT(*) FROM ledger") == "2"
        assert isinstance(rollback_transaction(connection), Ok)
        assert scalar(connection, "SELECT COUNT(*) FROM ledger") == "1"
        execute(connection, "INSERT INTO ledger VALUES (23)")
        assert isinstance(commit_transaction(connection), Ok)
        assert scalar(connection, "SELECT COUNT(*) FROM ledger") == "2"
        execute(connection, "INSERT INTO ledger VALUES (29)")
        assert scalar(connection, "SELECT COUNT(*) FROM ledger") == "3"
    finally:
        assert isinstance(close_connection(connection), Ok)
    assert isinstance(close_connection(connection), Ok)
    reopened = session(AdapterKind_Sqlite(), sqlite)
    try:
        assert scalar(reopened, "SELECT COUNT(*) FROM ledger") == "2", "disconnect committed pending work"
    finally:
        assert isinstance(close_connection(reopened), Ok)
    print("PASS: SQLite retained session, rollback, commit, disconnect rollback", flush=True)

    duck = root / "duck.db"
    duckdb.connect(str(duck)).close()
    connection = session(AdapterKind_DuckDb(), duck)
    try:
        execute(connection, "CREATE TABLE ledger(value INTEGER)")
        execute(connection, "INSERT INTO ledger VALUES (11)")
        assert scalar(connection, "SELECT COUNT(*) FROM ledger") == "1"
    finally:
        assert isinstance(close_connection(connection), Ok)
    reopened = session(AdapterKind_DuckDb(), duck)
    try:
        assert scalar(reopened, "SELECT value FROM ledger") == "11"
    finally:
        assert isinstance(close_connection(reopened), Ok)
    print("PASS: DuckDB retained session and persistence", flush=True)

    history = root / "history.db"
    initial = QueryRecord(run_at="2026-01-02T03:04:05.000000+00:00",
                          program="harlequin", connection="local", profile=Nothing(),
                          adapter="sqlite", sql="SELECT 1", status=QueryStatus_Ok(),
                          rows=Some(value=1), truncated=Some(value=False),
                          elapsed_ms=Some(value=25.0), error_text=Nothing())
    written = record_query(history, initial)
    assert isinstance(written, Ok) and written.value > 0, written
    scope = HistoryFilter(connection=Some(value="local"), search="",
                          program=Nothing(), status=Nothing())
    before = recent_queries(history, scope, Nothing())
    assert isinstance(before, Ok) and list(before.value) == [initial], before
    updated = update_query(history, written.value, QueryStatus_Error(),
                           Nothing(), Nothing(), Some(value=30.0),
                           Some(value="missing table"))
    assert isinstance(updated, Ok), updated
    after = recent_queries(history, scope, Nothing())
    assert isinstance(after, Ok) and len(after.value) == 1, after
    saved = after.value[0]
    assert isinstance(saved.status, QueryStatus_Error) and saved.rows == Nothing(), saved
    assert saved.elapsed_ms == Some(value=30.0) and saved.error_text == Some(value="missing table"), saved
    print("PASS: query history insert, read, update and reread through public facades", flush=True)
