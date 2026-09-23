import argparse
import sys
from typing import Final, Never

import psycopg
from psycopg.conninfo import make_conninfo
from cott_runtime import CottList

_PROMPT: Final[str] = "pgcli> "
_QUERY_FAILED: Final[str] = "query failed"
_CONNECTION_FAILED: Final[str] = "connection failed"
_IO_FAILED: Final[str] = "i/o failed"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pgcli-cott", add_help=False, exit_on_error=False)
    parser.add_argument("dsn", nargs="?", default=None)
    parser.add_argument("-h", "--host", default=None)
    parser.add_argument("-p", "--port", default=None)
    parser.add_argument("-U", "--username", default=None)
    parser.add_argument("-d", "--dbname", default=None)
    parser.add_argument("-c", "--command", default=None)
    parser.add_argument("--help", dest="show_help", action="store_true")
    return parser


def _cell(value: object) -> str:
    if value is None:
        return "NULL"
    return str(value)


def _execute(conn: psycopg.Connection[tuple[object, ...]], sql: str) -> bool:
    try:
        with conn.cursor() as cur:
            cur.execute(sql.encode("utf-8"))
            if cur.description is not None:
                lines = ["\t".join(col.name for col in cur.description)]
                for row in cur.fetchall():
                    lines.append("\t".join(_cell(v) for v in row))
                sys.stdout.write("\n".join(lines) + "\n")
            else:
                status = cur.statusmessage
                if status:
                    sys.stdout.write(status + "\n")
            sys.stdout.flush()
    except psycopg.Error:
        if conn.closed or conn.broken:
            raise
        sys.stderr.write(_QUERY_FAILED + "\n")
        return False
    return True


def _repl(conn: psycopg.Connection[tuple[object, ...]]) -> int:
    interactive = sys.stdin.isatty()
    ok = True
    while True:
        if interactive:
            sys.stdout.write(_PROMPT)
            sys.stdout.flush()
        line = sys.stdin.readline()
        if line == "":
            break
        text = line.strip()
        if text == "":
            continue
        if text == "\\q" or text == "quit":
            break
        if not _execute(conn, text):
            ok = False
    return 0 if ok else 1


def _main(argv: list[str]) -> int:
    parser = _parser()
    try:
        ns, extra = parser.parse_known_args(argv)
    except argparse.ArgumentError:
        sys.stderr.write(parser.format_usage())
        return 2
    if extra:
        sys.stderr.write(parser.format_usage())
        return 2
    if ns.show_help:
        sys.stdout.write(parser.format_help())
        return 0
    params: dict[str, str] = {}
    if ns.host:
        params["host"] = ns.host
    if ns.port:
        params["port"] = ns.port
    if ns.username:
        params["user"] = ns.username
    if ns.dbname:
        params["dbname"] = ns.dbname
    dsn: str = ns.dsn if ns.dsn else ""
    try:
        conninfo = make_conninfo(dsn, **params)
        conn = psycopg.connect(conninfo, autocommit=True, connect_timeout=10)
    except (psycopg.Error, OSError, ValueError):
        sys.stderr.write(_CONNECTION_FAILED + "\n")
        return 1
    try:
        if ns.command is not None:
            return 0 if _execute(conn, ns.command) else 1
        return _repl(conn)
    except psycopg.Error:
        sys.stderr.write(_CONNECTION_FAILED + "\n")
        return 1
    except (OSError, ValueError):
        sys.stderr.write(_IO_FAILED + "\n")
        return 1
    finally:
        conn.close()


def run(arguments: CottList[str]) -> Never:
    argv: list[str] = [a for a in arguments]
    try:
        code = _main(argv)
    except KeyboardInterrupt:
        code = 130
    sys.exit(code)
