import os
import json
import sqlite3
import tempfile
from pathlib import Path
import duckdb
from cott_runtime import CottList, Err, Ok
from real.harlequin.core import connect, disconnect, begin_transaction, commit_transaction, rollback_transaction, execute_statements
from real.harlequin.core_types import AdapterKind_Sqlite, AdapterKind_DuckDb, AdapterKind_Adbc, ConnectionRequest, Transaction, TransactionStatus_Active, TransactionStatus_Committed, TransactionStatus_RolledBack, Cell_Integer


def open_session(adapter, endpoint):
    outcome = connect(ConnectionRequest(adapter=adapter, endpoint=endpoint, settings=CottList(values=[]), read_only=False))
    assert isinstance(outcome, Ok), outcome
    return outcome.value


def execute(connection, sql):
    outcome = execute_statements(connection, sql, 100)
    assert isinstance(outcome, Ok), (sql, outcome)
    return outcome.value


def count(connection):
    result = execute(connection, 'SELECT COUNT(*) FROM ledger')
    cell = result.results[0].rows[0].values[0]
    assert isinstance(cell, Cell_Integer), cell
    return cell.value


def exercise(adapter, endpoint, label):
    connection = open_session(adapter, endpoint)
    try:
        execute(connection, 'CREATE TABLE ledger(value INTEGER)')
        first = begin_transaction(connection)
        assert isinstance(first, Ok) and isinstance(first.value.status, TransactionStatus_Active), first
        assert isinstance(begin_transaction(connection), Err), 'nested lease accepted'
        execute(connection, 'INSERT INTO ledger VALUES (1)')
        assert count(connection) == 1
        rolled = rollback_transaction(first.value)
        assert isinstance(rolled, Ok) and isinstance(rolled.value.status, TransactionStatus_RolledBack), rolled
        assert rolled.value.lease.unwrap() is first.value.lease.unwrap()
        assert count(connection) == 0, 'rollback did not affect the retained driver'
        second = begin_transaction(connection)
        assert isinstance(second, Ok) and isinstance(second.value.status, TransactionStatus_Active), second
        assert isinstance(commit_transaction(first.value), Err), 'stale lease accepted'
        execute(connection, 'INSERT INTO ledger VALUES (2)')
        committed = commit_transaction(second.value)
        assert isinstance(committed, Ok) and isinstance(committed.value.status, TransactionStatus_Committed), committed
        assert count(connection) == 1
        assert isinstance(rollback_transaction(second.value), Err), 'finished lease accepted'
        third = begin_transaction(connection)
        assert isinstance(third, Ok) and isinstance(third.value.status, TransactionStatus_Active), third
        execute(connection, 'INSERT INTO ledger VALUES (3)')
        assert count(connection) == 2
    finally:
        assert isinstance(disconnect(connection), Ok)
    assert isinstance(disconnect(connection), Ok), 'disconnect not idempotent'
    assert isinstance(execute_statements(connection, 'SELECT 1', 1), Err), 'closed connection reused'
    assert isinstance(commit_transaction(third.value), Err), 'closed lease accepted'
    reopened = open_session(adapter, endpoint)
    try:
        assert reopened.id != connection.id
        assert count(reopened) == 1, 'disconnect committed instead of rolling back'
        current = begin_transaction(reopened)
        assert isinstance(current, Ok), current
        foreign = Transaction(connection=reopened, lease=third.value.lease, status=TransactionStatus_Active())
        assert isinstance(commit_transaction(foreign), Err), 'wrong-owner lease accepted'
        assert isinstance(rollback_transaction(current.value), Ok)
    finally:
        assert isinstance(disconnect(reopened), Ok)
    print('PASS:', label, 'real commit, rollback, stale/nested/wrong-owner rejection and disconnect rollback', flush=True)


with tempfile.TemporaryDirectory(prefix='cott-live-data-') as directory:
    root = Path(directory)
    sqlite_file = root / 'sqlite.db'
    sqlite3.connect(sqlite_file).close()
    exercise(AdapterKind_Sqlite(), str(sqlite_file), 'SQLite')
    duck_file = root / 'duck.db'
    duckdb.connect(str(duck_file)).close()
    exercise(AdapterKind_DuckDb(), str(duck_file), 'DuckDB')
    driver = os.environ.get('COTT_ADBC_SQLITE_DRIVER')
    if driver:
        adbc_file = root / 'adbc.db'
        sqlite3.connect(adbc_file).close()
        endpoint = json.dumps({'driver': driver, 'uri': adbc_file.as_uri() + '?mode=rw'})
        exercise(AdapterKind_Adbc(), endpoint, 'ADBC SQLite')
    memory = open_session(AdapterKind_Sqlite(), ':memory:')
    try:
        execute(memory, 'CREATE TABLE ledger(value INTEGER)')
        execute(memory, 'INSERT INTO ledger VALUES (7)')
        assert count(memory) == 1, 'memory state lost between calls'
    finally:
        assert isinstance(disconnect(memory), Ok)
print('PASS: persistent in-memory session through public facades', flush=True)
