import sqlite3
import threading
from typing import Any, Final, Literal, cast

import cassandra.metadata
import duckdb
import mysql.connector
import psycopg
from cott_runtime import I64, Err, Nothing, Ok, Opaque, Result, Some
from google.cloud.bigquery.enums import StandardSqlTypeNames

from real.harlequin.adapters_types import AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Chdb, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino, Connection, QueryError, QueryError_Failed
from real.harlequin.catalog_types import Completion

_TITLE: Final[str] = "Harlequin could not load completions from your adapter."
_SESSION_TAG: Final[str] = "harlequin.session"
_MALFORMED: Final[str] = "The connection session is malformed."
_SESSION_KEYS: Final[str] = "adapter driver request cleanup lock closed transaction_mode modes active"
_SQLITE_KEYWORDS: Final[str] = "abort action add after all alter always analyze and as asc attach autoincrement before begin between by cascade case cast check collate column commit conflict constraint create cross current current_date current_time current_timestamp database default deferrable deferred delete desc detach distinct do drop each else end escape except exclude exclusive exists explain fail filter first following for foreign from full generated glob group groups having if ignore immediate in index indexed initially inner insert instead intersect into is isnull join key last left like limit match materialized natural no not nothing notnull null nulls of offset on or order others outer over partition plan pragma preceding primary query raise range recursive references regexp reindex release rename replace restrict returning right rollback row rows savepoint select set table temp temporary then ties to transaction trigger unbounded union unique update using vacuum values view virtual when where window with without"
_BIGQUERY_KEYWORDS: Final[str] = "ALL AND ANY ARRAY AS ASC ASSERT_ROWS_MODIFIED AT BETWEEN BY CASE CAST COLLATE CONTAINS CREATE CROSS CUBE CURRENT DEFAULT DEFINE DESC DISTINCT ELSE END ENUM ESCAPE EXCEPT EXCLUDE EXISTS EXTRACT FALSE FETCH FOLLOWING FOR FROM FULL GROUP GROUPING GROUPS HASH HAVING IF IGNORE IN INNER INTERSECT INTERVAL INTO IS JOIN LATERAL LEFT LIKE LIMIT LOOKUP MERGE NATURAL NEW NO NOT NULL NULLS OF ON OR ORDER OUTER OVER PARTITION PRECEDING PROTO QUALIFY RANGE RECURSIVE RESPECT RIGHT ROLLUP ROWS SELECT SET SOME STRUCT TABLESAMPLE THEN TO TREAT TRUE UNBOUNDED UNION UNNEST USING WHEN WHERE WINDOW WITH WITHIN"
_BIGQUERY_FUNCTIONS: Final[str] = "ABS ACOS ACOSH APPROX_COSINE_DISTANCE ARRAY_CONCAT ARRAY_FIRST ARRAY_LAST ARRAY_LENGTH ARRAY_REVERSE ARRAY_SLICE ARRAY_TO_STRING ASCII ASIN ASINH ATAN ATAN2 ATANH BIT_COUNT BYTE_LENGTH CBRT CEIL CEILING CHAR_LENGTH CHARACTER_LENGTH CHR COALESCE CODE_POINTS_TO_BYTES CODE_POINTS_TO_STRING COLLATE CONCAT COS COSH COSINE_DISTANCE COT COTH CSC CSCH CURRENT_DATE CURRENT_DATETIME CURRENT_TIME CURRENT_TIMESTAMP DATE DATE_ADD DATE_BUCKET DATE_DIFF DATE_FROM_UNIX_DATE DATE_SUB DATE_TRUNC DATETIME DATETIME_ADD DATETIME_BUCKET DATETIME_DIFF DATETIME_SUB DATETIME_TRUNC DIV EDIT_DISTANCE ENDS_WITH ERROR EUCLIDEAN_DISTANCE EXP EXTRACT FARM_FINGERPRINT FLOOR FORMAT FORMAT_DATE FORMAT_DATETIME FORMAT_TIME FORMAT_TIMESTAMP FROM_BASE32 FROM_BASE64 FROM_HEX GENERATE_ARRAY GENERATE_DATE_ARRAY GENERATE_TIMESTAMP_ARRAY GENERATE_UUID GREATEST IEEE_DIVIDE IF IFNULL INITCAP INSTR IS_INF IS_NAN JSON_EXTRACT JSON_EXTRACT_ARRAY JSON_EXTRACT_SCALAR JSON_QUERY JSON_QUERY_ARRAY JSON_TYPE JSON_VALUE JSON_VALUE_ARRAY JUSTIFY_DAYS JUSTIFY_HOURS JUSTIFY_INTERVAL LAST_DAY LEAST LEFT LENGTH LN LOG LOG10 LOWER LPAD LTRIM MAKE_INTERVAL MD5 MOD NET.HOST NET.IP_FROM_STRING NET.IP_TO_STRING NET.PUBLIC_SUFFIX NET.REG_DOMAIN NORMALIZE NORMALIZE_AND_CASEFOLD NULLIF OCTET_LENGTH PARSE_BIGNUMERIC PARSE_DATE PARSE_DATETIME PARSE_JSON PARSE_NUMERIC PARSE_TIME PARSE_TIMESTAMP POW POWER RAND RANGE_BUCKET REGEXP_CONTAINS REGEXP_EXTRACT REGEXP_EXTRACT_ALL REGEXP_INSTR REGEXP_REPLACE REGEXP_SUBSTR REPEAT REPLACE REVERSE RIGHT ROUND RPAD RTRIM SAFE_ADD SAFE_CAST SAFE_CONVERT_BYTES_TO_STRING SAFE_DIVIDE SAFE_MULTIPLY SAFE_NEGATE SAFE_SUBTRACT SEC SECH SESSION_USER SHA1 SHA256 SHA512 SIGN SIN SINH SOUNDEX SPLIT SQRT ST_AREA ST_ASGEOJSON ST_ASTEXT ST_CONTAINS ST_DISTANCE ST_GEOGFROMTEXT ST_GEOGPOINT ST_INTERSECTS ST_X ST_Y STARTS_WITH STRPOS SUBSTR SUBSTRING TAN TANH TIME TIME_ADD TIME_DIFF TIME_SUB TIME_TRUNC TIMESTAMP TIMESTAMP_ADD TIMESTAMP_BUCKET TIMESTAMP_DIFF TIMESTAMP_MICROS TIMESTAMP_MILLIS TIMESTAMP_SECONDS TIMESTAMP_SUB TIMESTAMP_TRUNC TO_BASE32 TO_BASE64 TO_CODE_POINTS TO_HEX TO_JSON TO_JSON_STRING TRANSLATE TRIM TRUNC UNICODE UNIX_DATE UNIX_MICROS UNIX_MILLIS UNIX_SECONDS UPPER"
_BIGQUERY_AGGREGATES: Final[str] = "ANY_VALUE APPROX_COUNT_DISTINCT APPROX_QUANTILES APPROX_TOP_COUNT APPROX_TOP_SUM ARRAY_AGG ARRAY_CONCAT_AGG AVG BIT_AND BIT_OR BIT_XOR CORR COUNT COUNTIF COVAR_POP COVAR_SAMP GROUPING HLL_COUNT.EXTRACT HLL_COUNT.INIT HLL_COUNT.MERGE HLL_COUNT.MERGE_PARTIAL LOGICAL_AND LOGICAL_OR MAX MAX_BY MIN MIN_BY STDDEV STDDEV_POP STDDEV_SAMP STRING_AGG SUM VAR_POP VAR_SAMP VARIANCE"
_TRINO_KEYWORDS: Final[str] = "ALTER AND AS BETWEEN BY CASE CAST CONSTRAINT CREATE CROSS CUBE CURRENT_CATALOG CURRENT_DATE CURRENT_PATH CURRENT_ROLE CURRENT_SCHEMA CURRENT_TIME CURRENT_TIMESTAMP CURRENT_USER DEALLOCATE DELETE DESCRIBE DISTINCT DROP ELSE END ESCAPE EXCEPT EXECUTE EXISTS EXTRACT FALSE FOR FROM FULL GROUP GROUPING HAVING IN INNER INSERT INTERSECT INTO IS JOIN JSON_ARRAY JSON_EXISTS JSON_OBJECT JSON_QUERY JSON_TABLE JSON_VALUE LEFT LIKE LISTAGG LOCALTIME LOCALTIMESTAMP NATURAL NORMALIZE NOT NULL ON OR ORDER OUTER PREPARE RECURSIVE RIGHT ROLLUP SELECT SKIP TABLE THEN TRIM TRUE UESCAPE UNION UNNEST USING VALUES WHEN WHERE WITH"
_DATABRICKS_KEYWORDS: Final[str] = "ALL ALTER AND ANTI ANY ARRAY AS AT AUTHORIZATION BETWEEN BOTH BY CASE CAST CHECK COLLATE COLUMN COMMIT CONSTRAINT CREATE CROSS CUBE CURRENT CURRENT_DATE CURRENT_TIME CURRENT_TIMESTAMP CURRENT_USER DELETE DESCRIBE DISTINCT DROP ELSE END ESCAPE EXCEPT EXISTS EXTERNAL EXTRACT FALSE FETCH FILTER FOR FOREIGN FROM FULL FUNCTION GLOBAL GRANT GROUP GROUPING HAVING IN INNER INSERT INTERSECT INTERVAL INTO IS JOIN LATERAL LEADING LEFT LIKE LOCAL MINUS NATURAL NO NOT NULL OF ON ONLY OR ORDER OUT OUTER OVERLAPS PARTITION POSITION PRIMARY RANGE REFERENCES REVOKE RIGHT ROLLBACK ROLLUP ROW ROWS SELECT SEMI SESSION_USER SET SOME START TABLE TABLESAMPLE THEN TIME TO TRAILING TRUE TRUNCATE UNION UNIQUE UNKNOWN UPDATE USER USING VALUES WHEN WHERE WINDOW WITH"
_NEBULA_KEYWORDS: Final[str] = "ACROSS ADD ALTER AND AS ASC ASCENDING BALANCE BOOL BY CASE CHANGE COMPACT CREATE DATE DATETIME DELETE DESC DESCENDING DESCRIBE DISTINCT DOUBLE DOWNLOAD DROP DURATION EDGE EDGES EXISTS EXPLAIN FALSE FETCH FIND FIXED_STRING FLOAT FLUSH FROM GEOGRAPHY GET GO GRANT IF IGNORE_EXISTED_INDEX IN INDEX INDEXES INGEST INSERT INT INT16 INT32 INT64 INT8 INTERSECT IS JOIN LEFT LIST LOOKUP MAP MATCH MINUS NO NOT NULL OF ON OR ORDER OVER OVERWRITE PATH PROP REBUILD RECOVER REMOVE RESTART RETURN REVERSELY REVOKE SET SHOW STEP STEPS STOP STRING SUBMIT TAG TAGS TIME TIMESTAMP TO TRUE UNION UNWIND UPDATE UPSERT UPTO USE VERTEX VERTICES WHEN WHERE WITH XOR YIELD"
_NEBULA_FUNCTIONS: Final[str] = "abs acos asin atan avg bit_and bit_or bit_xor cbrt ceil coalesce collect collect_set concat concat_ws cos count date datetime degrees dst duration e endNode exp exp2 floor hash head hypot id keys labels last left length log log10 log2 lower lpad ltrim max min nodes none_direct_dst none_direct_src now pi pow properties radians rand rand32 rand64 range rank reduce relationships replace reverse right round rpad rtrim sign sin size split sqrt src startNode std strcasecmp subgraph substr substring sum tags tail tan time timestamp toBoolean toFloat toInteger toLower toString toUpper trim type typeid udf_is_in upper vid"


def _fail(message: str) -> Result[Opaque[Literal["harlequin.completions"]], QueryError]:
    return Err(error=QueryError_Failed(title=_TITLE, message=message))


def _item(label: str, type_label: str, priority: I64, context: str | None) -> Completion:
    return Completion(label=label, value=label, type_label=type_label, priority=priority, context=Nothing() if context is None else Some(value=context))


def _words(words: str, type_label: str, priority: I64) -> list[Completion]:
    return [_item(word, type_label, priority, None) for word in words.split()]


def _rows(raw: object) -> list[list[object]]:
    rows: list[list[object]] = []
    if not isinstance(raw, list):
        return rows
    for row in cast(list[object], raw):
        if isinstance(row, tuple):
            rows.append(list(cast(tuple[object, ...], row)))
        elif isinstance(row, list):
            rows.append(list(cast(list[object], row)))
        else:
            rows.append([row])
    return rows


def _cursor_rows(driver: Any, sql: str) -> list[list[object]]:
    cursor: Any = driver.cursor()
    try:
        cursor.execute(sql)
        return _rows(cast(object, cursor.fetchall()))
    finally:
        cursor.close()


def _duckdb(conn: duckdb.DuckDBPyConnection) -> list[Completion]:
    out: list[Completion] = []
    for row in _rows(conn.execute("select distinct keyword_name, keyword_category = 'reserved' from duckdb_keywords()").fetchall()):
        out.append(_item(str(row[0]), "kw", 100 if row[1] is True else 1000, None))
    functions = "select distinct function_name, case function_type when 'pragma' then 'pragma' when 'macro' then 'macro' when 'table_macro' then 'macro' when 'aggregate' then 'agg' when 'table' then 'fn->T' else 'fn' end, schema_name from duckdb_functions() where database_name != 'temp'"
    for row in _rows(conn.execute(functions).fetchall()):
        schema = str(row[2]) if row[2] is not None else None
        out.append(_item(str(row[0]), str(row[1]), 1000, None if schema == "system" else schema))
    for row in _rows(conn.execute("select name from duckdb_settings()").fetchall()):
        out.append(_item(str(row[0]), "set", 2000, None))
    for row in _rows(conn.execute("select distinct type_name from duckdb_types() where database_name = 'system'").fetchall()):
        out.append(_item(str(row[0]), "type", 1000, None))
    custom = "select distinct type_name, schema_name from duckdb_types() where database_name != 'system' and not internal"
    for row in _rows(conn.execute(custom).fetchall()):
        out.append(_item(str(row[0]), "type", 1000, None if row[1] is None else str(row[1])))
    return out


def _sqlite(conn: sqlite3.Connection) -> list[Completion]:
    out = _words(_SQLITE_KEYWORDS, "kw", 100)
    pragmas = conn.execute("select name from pragma_pragma_list order by name")
    try:
        for row in _rows(pragmas.fetchall()):
            out.append(_item(str(row[0]), "pragma", 1000, None))
    finally:
        pragmas.close()
    sql = "select distinct name, case when type = 'w' then 'agg' else 'fn' end from pragma_function_list order by name"
    cursor = conn.execute(sql)
    try:
        for row in _rows(cursor.fetchall()):
            out.append(_item(str(row[0]), str(row[1]), 1000, None))
    finally:
        cursor.close()
    return out


def _postgres(conn: psycopg.Connection[tuple[object, ...]]) -> list[Completion]:
    out: list[Completion] = []
    with conn.cursor() as cur:
        cur.execute("select word, catcode = 'R' from pg_get_keywords()")
        for row in cur.fetchall():
            out.append(_item(str(row[0]), "kw", 100 if row[1] is True else 1000, None))
        cur.execute("select distinct routine_name, routine_type is null, routine_schema from information_schema.routines")
        for row in cur.fetchall():
            name = str(row[0])
            if len(name) >= 37 or name.startswith(("_", "pg_", "binary_upgrade_")):
                continue
            schema = None if row[2] is None else str(row[2])
            out.append(_item(name, "agg" if row[1] is True else "fn", 1000, None if schema == "pg_catalog" else schema))
        cur.execute("select name from pg_settings")
        for row in cur.fetchall():
            out.append(_item(str(row[0]), "set", 2000, None))
    return sorted(out, key=lambda c: c.label)


def _mysql(driver: Any) -> list[Completion]:
    out: list[Completion] = []
    for row in _cursor_rows(driver, "select WORD, RESERVED from information_schema.KEYWORDS"):
        reserved = row[1]
        out.append(_item(str(row[0]), "kw", 100 if isinstance(reserved, (int, bool)) and bool(reserved) else 1000, None))
    functions = "select distinct t.name from mysql.help_topic t join mysql.help_category c on t.help_category_id = c.help_category_id where c.name like '%Functions%'"
    try:
        rows = _cursor_rows(driver, functions)
    except mysql.connector.Error as error:
        detail: Any = error
        code = cast(object, detail.errno)
        # help_topic unreadable (no privilege / table missing) is optional; other driver errors propagate.
        if not isinstance(code, int) or code not in (1044, 1142, 1143, 1146):
            raise
        rows = []
    for row in rows:
        out.append(_item(str(row[0]), "fn", 1000, None))
    return out


def _bigquery() -> list[Completion]:
    out = [_item(member.name, "type", 1000, None) for member in StandardSqlTypeNames]
    return out + _words(_BIGQUERY_KEYWORDS, "kw", 100) + _words(_BIGQUERY_FUNCTIONS, "fn", 1000) + _words(_BIGQUERY_AGGREGATES, "agg", 1000)


def _show_functions(driver: Any, active: list[object]) -> list[Completion]:
    cursor: Any = driver.cursor()
    active.append(cast(object, cursor))
    try:
        cursor.execute("SHOW FUNCTIONS")
        rows = _rows(cast(object, cursor.fetchall()))
    finally:
        active.remove(cast(object, cursor))
        cursor.close()
    names = sorted({str(row[0]) for row in rows if row and row[0] is not None})
    return [_item(name, "fn", 1000, None) for name in names]


def _cassandra() -> list[Completion]:
    module: Any = cassandra.metadata
    keywords = cast(object, module.cql_keywords)
    reserved = cast(object, module.cql_keywords_reserved)
    reserved_set: set[str] = set()
    if isinstance(reserved, (set, frozenset)):
        reserved_set = {str(word) for word in cast(set[object], reserved)}
    words: set[str] = set(reserved_set)
    if isinstance(keywords, (set, frozenset)):
        words |= {str(word) for word in cast(set[object], keywords)}
    return [_item(word, "kw", 100 if word in reserved_set else 1000, None) for word in sorted(words)]


def _chdb() -> list[Completion]:
    out: list[Completion] = []
    out += _words("numbers numbers_mt file s3 url", "fn", 900)
    out += _words("remote cluster", "fn", 850)
    out += _words("mergeTreeIndex toDateTime64 toStartOfInterval quantile quantiles argMax argMin arrayJoin", "fn", 800)
    out += _words("PREWHERE FINAL SETTINGS FORMAT ENGINE MergeTree", "kw", 800)
    return out


def adapter_completions(connection: Connection) -> Result[Opaque[Literal["harlequin.completions"]], QueryError]:
    handle = connection.session
    if handle.tag != _SESSION_TAG:
        return _fail("The connection handle is not a Harlequin session.")
    raw = handle.unwrap()
    if not isinstance(raw, dict):
        return _fail(_MALFORMED)
    payload = cast(dict[str, object], raw)
    if set(payload.keys()) != set(_SESSION_KEYS.split()):
        return _fail(_MALFORMED)
    lock = payload["lock"]
    active_raw = payload["active"]
    if not isinstance(lock, type(threading.RLock())) or not isinstance(active_raw, list):
        return _fail(_MALFORMED)
    active = cast(list[object], active_raw)
    adapter = connection.adapter
    with lock:
        if payload["closed"] is not False:
            return _fail("The connection is closed.")
        driver = payload["driver"]
        try:
            if isinstance(adapter, AdapterKind_DuckDb):
                if not isinstance(driver, duckdb.DuckDBPyConnection):
                    return _fail(_MALFORMED)
                items = _duckdb(driver)
            elif isinstance(adapter, AdapterKind_Sqlite):
                if not isinstance(driver, sqlite3.Connection):
                    return _fail(_MALFORMED)
                items = _sqlite(driver)
            elif isinstance(adapter, AdapterKind_Postgres):
                if not isinstance(driver, psycopg.Connection):
                    return _fail(_MALFORMED)
                items = _postgres(cast(psycopg.Connection[tuple[object, ...]], driver))
            elif isinstance(adapter, AdapterKind_MySql):
                items = _mysql(driver)
            elif isinstance(adapter, AdapterKind_BigQuery):
                items = _bigquery()
            elif isinstance(adapter, AdapterKind_Trino):
                items = _words(_TRINO_KEYWORDS, "kw", 100) + _show_functions(driver, active)
            elif isinstance(adapter, AdapterKind_Databricks):
                items = _words(_DATABRICKS_KEYWORDS, "kw", 1000) + _show_functions(driver, active)
            elif isinstance(adapter, AdapterKind_Cassandra):
                items = _cassandra()
            elif isinstance(adapter, AdapterKind_NebulaGraph):
                items = _words(_NEBULA_KEYWORDS, "kw", 100) + _words(_NEBULA_FUNCTIONS, "fn", 1000)
            elif isinstance(adapter, AdapterKind_Chdb):
                items = _chdb()
            else:
                items = []
        except Exception as error:
            return _fail(str(error))
    return Ok(value=Opaque(tag="harlequin.completions", value=tuple(items)))
