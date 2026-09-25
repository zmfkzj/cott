import os
import re
import tempfile
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Final

import cott_runtime
from cott_runtime import CottContractViolation, CottList, Err, Ok, Result, Some, UNIT, Unit
from psycopg import sql
from real.pgcli import connect, edit_in_editor, execute_planned_query, export_query, format_query, import_delimited, load_favorites, load_history, plan_query, refresh_catalog, save_favorites
from real.pgcli_types import Catalog, CatalogRefreshRequest, ClientError, ClientError_ConnectionFailed, ClientError_ExportFailed, ClientError_FavoriteFailed, ClientError_ImportFailed, ClientError_InvalidCommand, CommandInvocation, CommandResult, EditorRequest, ExportRequest, Favorite, FavoriteStore, FormatRequest, ImportRequest, InputBuffer, MetaCommand_Connect, MetaCommand_ConnectionInfo, MetaCommand_Copy, MetaCommand_DeleteNamedQuery, MetaCommand_Describe, MetaCommand_Echo, MetaCommand_EditBuffer, MetaCommand_ExecuteBuffer, MetaCommand_ExecuteExpanded, MetaCommand_Expanded, MetaCommand_Favorite, MetaCommand_Help, MetaCommand_History, MetaCommand_ListDataTypes, MetaCommand_ListDatabases, MetaCommand_ListDefaultPrivileges, MetaCommand_ListDomains, MetaCommand_ListExtensions, MetaCommand_ListFavorites, MetaCommand_ListForeignTables, MetaCommand_ListFunctions, MetaCommand_ListIndexes, MetaCommand_ListMaterializedViews, MetaCommand_ListPrivileges, MetaCommand_ListRoles, MetaCommand_ListSchemas, MetaCommand_ListSequences, MetaCommand_ListTables, MetaCommand_ListTablespaces, MetaCommand_ListTextSearchConfigurations, MetaCommand_ListViews, MetaCommand_NamedQuery, MetaCommand_PrintBuffer, MetaCommand_PrintNamedQuery, MetaCommand_QueryOutputEcho, MetaCommand_Quit, MetaCommand_ReadFile, MetaCommand_ReadRelativeFile, MetaCommand_RefreshCatalog, MetaCommand_ResetBuffer, MetaCommand_SaveNamedQuery, MetaCommand_SetFormat, MetaCommand_SetPager, MetaCommand_ShowFunction, MetaCommand_SqlHelp, MetaCommand_Timing, MetaCommand_Unknown, MetaCommand_WriteBuffer, QueryRequest, QueryResult, SessionOptions, TableFormat, TableFormat_Aligned, TableFormat_Csv, TableFormat_Html, TableFormat_Json, TableFormat_JsonLines, TableFormat_Latex, TableFormat_Markdown, TableFormat_Tsv, TableFormat_Vertical, TransactionMode_ReadOnly

_HELP: Final[str] = "\\q  Quit.\n\\refresh  Refresh the completion catalog.\n\\?  Show help.\n\\h  SQL command documentation link.\n\\T  Set the output format.\n\\c  Connect to a database.\n\\conninfo  Show connection information.\n\\copy  Import or export CSV.\n\\d  Describe relations.\n\\dD  List domains.\n\\dE  List foreign tables.\n\\dF  List text search configurations.\n\\dT  List data types.\n\\db  List tablespaces.\n\\ddp  List default privileges.\n\\df  List functions.\n\\di  List indexes.\n\\dm  List materialized views.\n\\dn  List schemas.\n\\dp  List privileges.\n\\ds  List sequences.\n\\dt  List tables.\n\\du  List roles.\n\\dv  List views.\n\\dx  List extensions.\n\\l  List databases.\n\\sf  Show function definitions.\n\\e  Edit the query buffer.\n\\echo  Print text.\n\\i  Read a file into the buffer.\n\\ir  Read a relative file into the buffer.\n\\n  Run a named query.\n\\nd  Delete a named query.\n\\np  Print a named query.\n\\ns  Save a named query.\n\\pager  Set pager usage.\n\\qecho  Print text to query output.\n\\timing  Toggle timing.\n\\x  Toggle expanded display.\n\\g  Execute the buffer.\n\\gx  Execute the buffer with expanded output.\n\\p  Print the buffer.\n\\r  Reset the buffer.\n\\w  Write the buffer to a file.\n\\history  Show history.\n\\fav  Save the buffer as a favorite.\n\\favs  List favorites.\n\\unfav  Delete a favorite."
_DOMAINS_SQL: Final[str] = "SELECT n.nspname, t.typname, pg_catalog.format_type(t.typbasetype, t.typtypmod) FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace WHERE t.typtype = 'd' ORDER BY 1, 2"
_FOREIGN_SQL: Final[str] = "SELECT n.nspname, c.relname, s.srvname FROM pg_catalog.pg_foreign_table f JOIN pg_catalog.pg_class c ON c.oid = f.ftrelid JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace JOIN pg_catalog.pg_foreign_server s ON s.oid = f.ftserver ORDER BY 1, 2"
_TSCONFIG_SQL: Final[str] = "SELECT n.nspname, c.cfgname FROM pg_catalog.pg_ts_config c JOIN pg_catalog.pg_namespace n ON n.oid = c.cfgnamespace ORDER BY 1, 2"
_TYPES_SQL: Final[str] = "SELECT n.nspname, pg_catalog.format_type(t.oid, NULL) FROM pg_catalog.pg_type t JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace WHERE t.typelem = 0 AND t.typrelid = 0 ORDER BY 1, 2"
_TABLESPACES_SQL: Final[str] = "SELECT spcname, pg_catalog.pg_get_userbyid(spcowner), pg_catalog.pg_tablespace_location(oid) FROM pg_catalog.pg_tablespace ORDER BY 1"
_DEFAULT_PRIVS_SQL: Final[str] = "SELECT pg_catalog.pg_get_userbyid(d.defaclrole), COALESCE(n.nspname, ''), d.defaclobjtype::text, COALESCE(pg_catalog.array_to_string(d.defaclacl, E'\\n'), '') FROM pg_catalog.pg_default_acl d LEFT JOIN pg_catalog.pg_namespace n ON n.oid = d.defaclnamespace ORDER BY 1, 2, 3"
_INDEXES_SQL: Final[str] = "SELECT schemaname, indexname, tablename FROM pg_catalog.pg_indexes ORDER BY 1, 2"
_PRIVILEGES_SQL: Final[str] = "SELECT n.nspname, c.relname, COALESCE(pg_catalog.array_to_string(c.relacl, E'\\n'), '') FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE c.relkind IN ('r', 'v', 'm', 'S', 'f', 'p') ORDER BY 1, 2"
_FUNCTIONS_SQL: Final[str] = "SELECT n.nspname, p.proname, pg_catalog.pg_get_functiondef(p.oid) FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace WHERE p.prokind IN ('f', 'p', 'w') AND n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg\\_toast%' AND n.nspname NOT LIKE 'pg\\_temp%' ORDER BY 1, 2"
_INACTIVE: Final[str] = "fixture adapters are inactive"


def _matches(pattern: str, schema: str, name: str) -> bool:
    if pattern == "":
        return True
    parts: list[str] = []
    for ch in pattern:
        if ch == "*":
            parts.append(".*")
        elif ch == "?":
            parts.append(".")
        else:
            parts.append(re.escape(ch))
    subject = f"{schema}.{name}" if "." in pattern else name
    return re.fullmatch("".join(parts), subject, re.DOTALL) is not None


def _table(columns: list[str], rows: list[list[str]], options: SessionOptions) -> str:
    query = QueryResult(columns=CottList(values=columns), rows=CottList(values=[CottList(values=r) for r in rows]))
    return format_query(FormatRequest(query=query, format=options.format, terminal_width=80, max_column_width=0, max_rows=options.max_rows)).rendered.text


def _format_name(fmt: TableFormat) -> str:
    if isinstance(fmt, TableFormat_Aligned):
        return "aligned"
    if isinstance(fmt, TableFormat_Csv):
        return "csv"
    if isinstance(fmt, TableFormat_Tsv):
        return "tsv"
    if isinstance(fmt, TableFormat_Json):
        return "json"
    if isinstance(fmt, TableFormat_JsonLines):
        return "jsonl"
    if isinstance(fmt, TableFormat_Html):
        return "html"
    if isinstance(fmt, TableFormat_Latex):
        return "latex"
    if isinstance(fmt, TableFormat_Markdown):
        return "markdown"
    return "vertical"


def _done(buffer: InputBuffer, options: SessionOptions, catalog: Catalog, output: str, quit: bool) -> Result[CommandResult, ClientError]:
    password = options.connection.settings.password
    if password != "" and password in output:
        output = output.replace(password, "********")
    return Ok(value=CommandResult(buffer=buffer, options=options, catalog=catalog, output=output, quit=quit))


def _server_rows(options: SessionOptions, sql: str) -> Result[list[list[str]], ClientError]:
    executed = execute_planned_query(QueryRequest(connection=options.connection, sql=sql, max_rows=options.max_rows, transaction=TransactionMode_ReadOnly(), timing=False))
    if isinstance(executed, Err):
        return executed
    return Ok(value=[[cell for cell in row] for row in executed.value.result.rows])


def _server_list(options: SessionOptions, sql: str, columns: list[str], schema_index: int, name_index: int, pattern: str) -> Result[str, ClientError]:
    fetched = _server_rows(options, sql)
    if isinstance(fetched, Err):
        return fetched
    kept: list[list[str]] = []
    for row in fetched.value:
        cells = row + [""] * (len(columns) - len(row))
        schema = cells[schema_index] if schema_index >= 0 else ""
        if _matches(pattern, schema, cells[name_index]):
            kept.append(cells[: len(columns)])
    return Ok(value=_table(columns, kept, options))


def _execute(options: SessionOptions, buffer: InputBuffer, expanded: bool) -> Result[str, ClientError]:
    planned = plan_query(buffer)
    if isinstance(planned, Err):
        return planned
    executed = execute_planned_query(QueryRequest(connection=options.connection, sql=planned.value.sql, max_rows=options.max_rows, transaction=options.transaction, timing=options.timing))
    if isinstance(executed, Err):
        return executed
    fmt: TableFormat = TableFormat_Vertical() if expanded else options.format
    rendered = format_query(FormatRequest(query=executed.value.result, format=fmt, terminal_width=80, max_column_width=0, max_rows=options.max_rows)).rendered.text
    parts: list[str] = []
    if rendered != "":
        parts.append(rendered)
    if executed.value.status != "":
        parts.append(executed.value.status)
    if options.timing:
        parts.append(f"Time: {executed.value.elapsed_ms} ms")
    return Ok(value="\n".join(parts))


def _read_file(path: Path, source: Path) -> Result[str, ClientError]:
    try:
        data = cott_runtime._cott_fixture_read(path)
    except CottContractViolation as violation:
        if violation.message != _INACTIVE:
            return Err(error=ClientError_ImportFailed(path=path, message="file could not be read"))
        try:
            with open(source, "rb") as handle:
                data = handle.read()
        except OSError:
            return Err(error=ClientError_ImportFailed(path=path, message="file could not be read"))
    except Exception:
        return Err(error=ClientError_ImportFailed(path=path, message="file could not be read"))
    try:
        return Ok(value=data.decode("utf-8"))
    except UnicodeDecodeError:
        return Err(error=ClientError_ImportFailed(path=path, message="file could not be read"))


def _write_file(path: Path, text: str) -> Result[Unit, ClientError]:
    try:
        data = text.encode("utf-8")
    except UnicodeEncodeError:
        return Err(error=ClientError_ExportFailed(path=path, message="file could not be written"))
    try:
        cott_runtime._cott_fixture_replace(path, data)
        return Ok(value=UNIT)
    except CottContractViolation as violation:
        if violation.message != _INACTIVE:
            return Err(error=ClientError_ExportFailed(path=path, message="file could not be written"))
        try:
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(text)
            return Ok(value=UNIT)
        except OSError:
            return Err(error=ClientError_ExportFailed(path=path, message="file could not be written"))
    except Exception:
        return Err(error=ClientError_ExportFailed(path=path, message="file could not be written"))


def _quote_table(table: str) -> str:
    return sql.Identifier(*table.split(".")).as_string()


def _favorites(options: SessionOptions) -> Result[tuple[FavoriteStore, list[Favorite]], ClientError]:
    store = options.favorites
    if not isinstance(store, Some):
        return Err(error=ClientError_FavoriteFailed(name=""))
    loaded = load_favorites(store.value)
    if isinstance(loaded, Err):
        return loaded
    return Ok(value=(store.value, [f for f in loaded.value]))


def _save_favorite(options: SessionOptions, name: str, sql: str) -> Result[str, ClientError]:
    got = _favorites(options)
    if isinstance(got, Err):
        return got
    store, favorites = got.value
    updated: list[Favorite] = []
    found = False
    for fav in favorites:
        if fav.name == name:
            updated.append(Favorite(name=fav.name, sql=sql, tags=fav.tags))
            found = True
        else:
            updated.append(fav)
    if not found:
        updated.append(Favorite(name=name, sql=sql, tags=CottList(values=[])))
    saved = save_favorites(store, CottList(values=updated))
    if isinstance(saved, Err):
        return saved
    return Ok(value=f'Saved favorite "{name}".')


def _delete_favorite(options: SessionOptions, name: str) -> Result[str, ClientError]:
    got = _favorites(options)
    if isinstance(got, Err):
        return got
    store, favorites = got.value
    remaining = [f for f in favorites if f.name != name]
    if len(remaining) == len(favorites):
        return Err(error=ClientError_FavoriteFailed(name=name))
    saved = save_favorites(store, CottList(values=remaining))
    if isinstance(saved, Err):
        return saved
    return Ok(value=f'Deleted favorite "{name}".')


def _find_favorite(options: SessionOptions, name: str) -> Result[Favorite, ClientError]:
    got = _favorites(options)
    if isinstance(got, Err):
        return got
    for fav in got.value[1]:
        if fav.name == name:
            return Ok(value=fav)
    return Err(error=ClientError_FavoriteFailed(name=name))


def _relations(catalog: Catalog, kinds: tuple[str, ...], pattern: str, options: SessionOptions) -> str:
    rows = [[r.schema, r.name, r.kind] for r in catalog.relations if r.kind in kinds and _matches(pattern, r.schema, r.name)]
    return _table(["Schema", "Name", "Type"], rows, options)


def _text(result: Result[str, ClientError], buffer: InputBuffer, options: SessionOptions, catalog: Catalog) -> Result[CommandResult, ClientError]:
    if isinstance(result, Err):
        return result
    return _done(buffer, options, catalog, result.value, False)


def run_meta_command(invocation: CommandInvocation, options: SessionOptions, catalog: Catalog) -> Result[CommandResult, ClientError]:
    command = invocation.command
    buffer = invocation.buffer
    if isinstance(command, MetaCommand_Unknown):
        return Err(error=ClientError_InvalidCommand(source=command.source))
    if isinstance(command, MetaCommand_Quit):
        return _done(buffer, options, catalog, "", True)
    if isinstance(command, MetaCommand_Help):
        return _done(buffer, options, catalog, _HELP, False)
    if isinstance(command, MetaCommand_SqlHelp):
        if command.topic == "":
            url = "https://www.postgresql.org/docs/current/sql-commands.html"
        else:
            url = "https://www.postgresql.org/docs/current/sql-" + "".join(command.topic.lower().split(" ")) + ".html"
        return _done(buffer, options, catalog, url, False)
    if isinstance(command, MetaCommand_SetFormat):
        return _done(buffer, replace(options, format=command.format), catalog, "Output format: " + _format_name(command.format), False)
    if isinstance(command, MetaCommand_Timing):
        timing = not options.timing
        return _done(buffer, replace(options, timing=timing), catalog, "Timing is on." if timing else "Timing is off.", False)
    if isinstance(command, MetaCommand_Expanded):
        was_vertical = isinstance(options.format, TableFormat_Vertical)
        fmt: TableFormat = TableFormat_Aligned() if was_vertical else TableFormat_Vertical()
        return _done(buffer, replace(options, format=fmt), catalog, "Expanded display is off." if was_vertical else "Expanded display is on.", False)
    if isinstance(command, MetaCommand_SetPager):
        return _done(buffer, replace(options, pager=command.enabled), catalog, "Pager usage is on." if command.enabled else "Pager usage is off.", False)
    if isinstance(command, MetaCommand_ConnectionInfo):
        s = options.connection.settings
        return _done(buffer, options, catalog, f'You are connected to database "{s.database}" as user "{s.user}" on host "{s.host}" at port "{s.port}".', False)
    if isinstance(command, MetaCommand_Echo):
        return _done(buffer, options, catalog, command.text, False)
    if isinstance(command, MetaCommand_QueryOutputEcho):
        return _done(buffer, options, catalog, command.text, False)
    if isinstance(command, MetaCommand_PrintBuffer):
        return _done(buffer, options, catalog, buffer.text if buffer.text != "" else "Query buffer is empty.", False)
    if isinstance(command, MetaCommand_ResetBuffer):
        return _done(InputBuffer(text="", cursor=0, multiline=buffer.multiline), options, catalog, "Query buffer reset (cleared).", False)
    if isinstance(command, MetaCommand_Describe):
        if command.pattern == "":
            rows = [[r.schema, r.name, r.kind] for r in catalog.relations]
            return _done(buffer, options, catalog, _table(["Schema", "Name", "Type"], rows, options), False)
        columns: list[list[str]] = []
        for r in catalog.relations:
            if _matches(command.pattern, r.schema, r.name):
                for c in r.columns:
                    columns.append([r.schema, r.name, c.name])
        return _done(buffer, options, catalog, _table(["Schema", "Relation", "Column"], columns, options), False)
    if isinstance(command, MetaCommand_ListTables):
        return _done(buffer, options, catalog, _relations(catalog, ("table", "partitioned table"), command.pattern, options), False)
    if isinstance(command, MetaCommand_ListViews):
        return _done(buffer, options, catalog, _relations(catalog, ("view",), command.pattern, options), False)
    if isinstance(command, MetaCommand_ListMaterializedViews):
        return _done(buffer, options, catalog, _relations(catalog, ("materialized view",), command.pattern, options), False)
    if isinstance(command, MetaCommand_ListSequences):
        return _done(buffer, options, catalog, _relations(catalog, ("sequence",), command.pattern, options), False)
    if isinstance(command, MetaCommand_ListSchemas):
        return _done(buffer, options, catalog, _table(["Name"], [[s] for s in catalog.schemas if _matches(command.pattern, "", s)], options), False)
    if isinstance(command, MetaCommand_ListFunctions):
        routines = [[rt.schema, rt.name, rt.result_type, rt.arguments] for rt in catalog.routines if _matches(command.pattern, rt.schema, rt.name)]
        return _done(buffer, options, catalog, _table(["Schema", "Name", "Result data type", "Argument data types"], routines, options), False)
    if isinstance(command, MetaCommand_ListRoles):
        return _done(buffer, options, catalog, _table(["Name"], [[v] for v in catalog.roles], options), False)
    if isinstance(command, MetaCommand_ListExtensions):
        return _done(buffer, options, catalog, _table(["Name"], [[v] for v in catalog.extensions], options), False)
    if isinstance(command, MetaCommand_ListDatabases):
        return _done(buffer, options, catalog, _table(["Name"], [[v] for v in catalog.databases], options), False)
    if isinstance(command, MetaCommand_ListDomains):
        return _text(_server_list(options, _DOMAINS_SQL, ["Schema", "Name", "Type"], 0, 1, command.pattern), buffer, options, catalog)
    if isinstance(command, MetaCommand_ListForeignTables):
        return _text(_server_list(options, _FOREIGN_SQL, ["Schema", "Name", "Server"], 0, 1, command.pattern), buffer, options, catalog)
    if isinstance(command, MetaCommand_ListTextSearchConfigurations):
        return _text(_server_list(options, _TSCONFIG_SQL, ["Schema", "Name"], 0, 1, command.pattern), buffer, options, catalog)
    if isinstance(command, MetaCommand_ListDataTypes):
        return _text(_server_list(options, _TYPES_SQL, ["Schema", "Name"], 0, 1, command.pattern), buffer, options, catalog)
    if isinstance(command, MetaCommand_ListTablespaces):
        return _text(_server_list(options, _TABLESPACES_SQL, ["Name", "Owner", "Location"], -1, 0, command.pattern), buffer, options, catalog)
    if isinstance(command, MetaCommand_ListDefaultPrivileges):
        return _text(_server_list(options, _DEFAULT_PRIVS_SQL, ["Owner", "Schema", "Type", "Privileges"], -1, 1, command.pattern), buffer, options, catalog)
    if isinstance(command, MetaCommand_ListIndexes):
        return _text(_server_list(options, _INDEXES_SQL, ["Schema", "Name", "Table"], 0, 1, command.pattern), buffer, options, catalog)
    if isinstance(command, MetaCommand_ListPrivileges):
        return _text(_server_list(options, _PRIVILEGES_SQL, ["Schema", "Name", "Privileges"], 0, 1, command.pattern), buffer, options, catalog)
    if isinstance(command, MetaCommand_ShowFunction):
        fetched = _server_rows(options, _FUNCTIONS_SQL)
        if isinstance(fetched, Err):
            return fetched
        definitions = [row[2] for row in fetched.value if len(row) >= 3 and _matches(command.pattern, row[0], row[1])]
        output = "\n\n".join(definitions) if definitions else f'No function matches "{command.pattern}".'
        return _done(buffer, options, catalog, output, False)
    if isinstance(command, MetaCommand_Connect):
        candidate = replace(options.connection, settings=replace(options.connection.settings, database=command.database))
        receipt = connect(candidate)
        if isinstance(receipt, Err):
            return Err(error=ClientError_ConnectionFailed(message="connection failed"))
        refreshed = refresh_catalog(CatalogRefreshRequest(connection=candidate, include_system=False, limit=options.catalog_limit))
        if isinstance(refreshed, Err):
            return refreshed
        return _done(buffer, replace(options, connection=candidate), refreshed.value, f'You are now connected to database "{receipt.value.database}" as user "{receipt.value.user}".', False)
    if isinstance(command, MetaCommand_RefreshCatalog):
        refreshed = refresh_catalog(CatalogRefreshRequest(connection=options.connection, include_system=False, limit=options.catalog_limit))
        if isinstance(refreshed, Err):
            return refreshed
        relations = sum(1 for _ in refreshed.value.relations)
        routines_count = sum(1 for _ in refreshed.value.routines)
        return _done(buffer, options, refreshed.value, f"Catalog refreshed: {relations} relations, {routines_count} routines.", False)
    if isinstance(command, MetaCommand_ExecuteBuffer) or isinstance(command, MetaCommand_ExecuteExpanded):
        ran = _execute(options, buffer, isinstance(command, MetaCommand_ExecuteExpanded))
        return _text(ran, InputBuffer(text="", cursor=0, multiline=buffer.multiline), options, catalog)
    if isinstance(command, MetaCommand_EditBuffer):
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or "vi"
        temporary = Path(tempfile.gettempdir()) / f"pgcli-edit-{uuid.uuid4().hex}.sql"
        edited = edit_in_editor(EditorRequest(buffer=buffer, editor=editor, temporary_path=temporary))
        if isinstance(edited, Err):
            return edited
        return _done(edited.value, options, catalog, "", False)
    if isinstance(command, MetaCommand_ReadFile) or isinstance(command, MetaCommand_ReadRelativeFile):
        source = command.path if isinstance(command, MetaCommand_ReadFile) else Path.cwd() / command.path
        read = _read_file(command.path, source)
        if isinstance(read, Err):
            return read
        return _done(InputBuffer(text=read.value, cursor=len(read.value), multiline=buffer.multiline), options, catalog, "", False)
    if isinstance(command, MetaCommand_WriteBuffer):
        written = _write_file(command.path, buffer.text)
        if isinstance(written, Err):
            return written
        return _done(buffer, options, catalog, f'Wrote query buffer to "{os.fspath(command.path)}".', False)
    if isinstance(command, MetaCommand_Copy):
        if command.from_file:
            transferred = import_delimited(options.connection, ImportRequest(table=command.table, source=command.path, delimiter=",", header=True, null_text="", max_rows=1000000))
        else:
            transferred = export_query(options.connection, ExportRequest(sql="SELECT * FROM " + _quote_table(command.table), target=command.path, format=TableFormat_Csv(), delimiter=",", header=True, max_rows=1000000))
        if isinstance(transferred, Err):
            return transferred
        return _done(buffer, options, catalog, f"COPY {transferred.value.rows}", False)
    if isinstance(command, MetaCommand_History):
        policy = options.history
        if not isinstance(policy, Some):
            return _done(buffer, options, catalog, "History is disabled.", False)
        loaded = load_history(policy.value)
        if isinstance(loaded, Err):
            return loaded
        lines = [f"{n}  {entry.sql}" for n, entry in enumerate(loaded.value, 1) if command.pattern in entry.sql]
        return _done(buffer, options, catalog, "\n".join(lines), False)
    if isinstance(command, MetaCommand_NamedQuery):
        found = _find_favorite(options, command.name)
        if isinstance(found, Err):
            return found
        text = found.value.sql
        arguments = [a for a in command.arguments]
        for k in range(len(arguments), 0, -1):
            text = text.replace(f"${k}", arguments[k - 1])
        named = InputBuffer(text=text, cursor=len(text), multiline=buffer.multiline)
        return _text(_execute(options, named, False), buffer, options, catalog)
    if isinstance(command, MetaCommand_SaveNamedQuery):
        return _text(_save_favorite(options, command.name, command.sql), buffer, options, catalog)
    if isinstance(command, MetaCommand_Favorite):
        return _text(_save_favorite(options, command.name, buffer.text), buffer, options, catalog)
    if isinstance(command, MetaCommand_DeleteNamedQuery):
        return _text(_delete_favorite(options, command.name), buffer, options, catalog)
    if isinstance(command, MetaCommand_PrintNamedQuery):
        found = _find_favorite(options, command.name)
        if isinstance(found, Err):
            return found
        return _done(buffer, options, catalog, f"{command.name}: {found.value.sql}", False)
    if isinstance(command, MetaCommand_ListFavorites):
        got = _favorites(options)
        if isinstance(got, Err):
            return got
        rows = [[f.name, f.sql] for f in got.value[1] if _matches(command.pattern, "", f.name)]
        return _done(buffer, options, catalog, _table(["Name", "Query"], rows, options), False)
    return _text(_delete_favorite(options, command.name), buffer, options, catalog)
