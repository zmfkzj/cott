from cott_runtime import Err, Ok, Result
from real.pgcli_types import (
    Catalog,
    ClientError,
    ClientError_CatalogFailed,
    ClientError_EditorFailed,
    ClientError_ExportFailed,
    ClientError_FavoriteFailed,
    ClientError_HistoryFailed,
    ClientError_ImportFailed,
    ClientError_InvalidCommand,
    ClientError_NotificationFailed,
    ClientError_QueryFailed,
    CommandInvocation,
    CommandResult,
    InputBuffer,
    MetaCommand_ClearOutput,
    MetaCommand_Connect,
    MetaCommand_ConnectionInfo,
    MetaCommand_Copy,
    MetaCommand_DeleteFavorite,
    MetaCommand_DeleteNamedQuery,
    MetaCommand_Describe,
    MetaCommand_Echo,
    MetaCommand_EditBuffer,
    MetaCommand_ExecuteBuffer,
    MetaCommand_ExecuteExpanded,
    MetaCommand_Expanded,
    MetaCommand_Favorite,
    MetaCommand_Help,
    MetaCommand_History,
    MetaCommand_ListDatabases,
    MetaCommand_ListDataTypes,
    MetaCommand_ListDefaultPrivileges,
    MetaCommand_ListDomains,
    MetaCommand_ListExtensions,
    MetaCommand_ListFavorites,
    MetaCommand_ListForeignTables,
    MetaCommand_ListFunctions,
    MetaCommand_ListIndexes,
    MetaCommand_ListMaterializedViews,
    MetaCommand_ListNotifications,
    MetaCommand_ListPrivileges,
    MetaCommand_ListRoles,
    MetaCommand_ListSchemas,
    MetaCommand_ListSequences,
    MetaCommand_ListTables,
    MetaCommand_ListTablespaces,
    MetaCommand_ListTextSearchConfigurations,
    MetaCommand_ListViews,
    MetaCommand_NamedQuery,
    MetaCommand_Password,
    MetaCommand_PrintBuffer,
    MetaCommand_PrintNamedQuery,
    MetaCommand_QueryOutputEcho,
    MetaCommand_Quit,
    MetaCommand_ReadFile,
    MetaCommand_ReadRelativeFile,
    MetaCommand_RefreshCatalog,
    MetaCommand_ResetBuffer,
    MetaCommand_SaveNamedQuery,
    MetaCommand_SetFormat,
    MetaCommand_SetLogFile,
    MetaCommand_SetOptions,
    MetaCommand_SetOutput,
    MetaCommand_SetPager,
    MetaCommand_Shell,
    MetaCommand_ShowFunction,
    MetaCommand_SqlHelp,
    MetaCommand_Timing,
    MetaCommand_Unknown,
    MetaCommand_VerboseErrors,
    MetaCommand_Watch,
    MetaCommand_WriteBuffer,
    SessionOptions,
    TableFormat,
    TableFormat_Aligned,
    TableFormat_Csv,
    TableFormat_Html,
    TableFormat_Json,
    TableFormat_JsonLines,
    TableFormat_Latex,
    TableFormat_Markdown,
    TableFormat_Tsv,
)


def _success(buffer: InputBuffer, output: str, quit: bool) -> Result[CommandResult, ClientError]:
    if not quit:
        text_length = len(buffer.text)
        if buffer.cursor > text_length:
            buffer = InputBuffer(text=buffer.text, cursor=text_length, multiline=buffer.multiline)
    return Ok(value=CommandResult(buffer=buffer, output=output, quit=quit))


def _matches(value: str, pattern: str) -> bool:
    return pattern == "" or pattern.casefold() in value.casefold()


def _format_name(format: TableFormat) -> str:
    if isinstance(format, TableFormat_Aligned):
        return "aligned"
    if isinstance(format, TableFormat_Csv):
        return "csv"
    if isinstance(format, TableFormat_Tsv):
        return "tsv"
    if isinstance(format, TableFormat_Json):
        return "json"
    if isinstance(format, TableFormat_JsonLines):
        return "jsonlines"
    if isinstance(format, TableFormat_Html):
        return "html"
    if isinstance(format, TableFormat_Latex):
        return "latex"
    if isinstance(format, TableFormat_Markdown):
        return "markdown"
    return "vertical"


def run_meta_command(invocation: CommandInvocation, options: SessionOptions, catalog: Catalog) -> Result[CommandResult, ClientError]:
    command = invocation.command
    buffer = invocation.buffer

    if isinstance(command, MetaCommand_Quit):
        return _success(buffer, "", True)
    if isinstance(command, MetaCommand_Unknown):
        return Err(error=ClientError_InvalidCommand(source=command.source))
    if isinstance(command, MetaCommand_Shell):
        return Err(error=ClientError_InvalidCommand(source=command.command))
    if isinstance(command, MetaCommand_Help):
        return _success(
            buffer,
            "Meta commands:\n"
            "  \\q             quit\n"
            "  \\?             show help\n"
            "  \\c DATABASE    connect to a database\n"
            "  \\d [PATTERN]   describe relations\n"
            "  \\dt [PATTERN]  list tables\n"
            "  \\dv [PATTERN]  list views\n"
            "  \\df [PATTERN]  list functions\n"
            "  \\l             list databases\n"
            "  \\x             toggle expanded display\n"
            "  \\g             execute the query buffer\n"
            "  \\p             print the query buffer\n"
            "  \\r             reset the query buffer",
            False,
        )
    if isinstance(command, MetaCommand_SqlHelp):
        if command.topic == "":
            return _success(buffer, "SQL help requires a topic.", False)
        return _success(buffer, "SQL help for " + command.topic, False)
    if isinstance(command, MetaCommand_Echo):
        return _success(buffer, command.text, False)
    if isinstance(command, MetaCommand_QueryOutputEcho):
        return _success(buffer, command.text, False)
    if isinstance(command, MetaCommand_PrintBuffer):
        return _success(buffer, buffer.text, False)
    if isinstance(command, MetaCommand_ResetBuffer):
        return _success(InputBuffer(text="", cursor=0, multiline=buffer.multiline), "", False)
    if isinstance(command, MetaCommand_SetFormat):
        return _success(buffer, "Output format is " + _format_name(command.format) + ".", False)
    if isinstance(command, MetaCommand_SetPager):
        return _success(buffer, "Pager is " + ("on." if command.enabled else "off."), False)
    if isinstance(command, MetaCommand_SetOptions):
        return _success(buffer, command.key + " = " + command.value, False)
    if isinstance(command, MetaCommand_Timing):
        return _success(buffer, "Timing is " + ("off." if options.timing else "on."), False)
    if isinstance(command, MetaCommand_VerboseErrors):
        return _success(buffer, "Verbose errors are " + ("on." if command.enabled else "off."), False)
    if isinstance(command, MetaCommand_Expanded):
        return _success(buffer, "Expanded display toggled.", False)
    if isinstance(command, MetaCommand_SetOutput):
        return _success(buffer, "Output is redirected to " + str(command.path) + ".", False)
    if isinstance(command, MetaCommand_ClearOutput):
        return _success(buffer, "Output redirection cleared.", False)
    if isinstance(command, MetaCommand_SetLogFile):
        return _success(buffer, "Log file is " + str(command.path) + ".", False)
    if isinstance(command, MetaCommand_ConnectionInfo):
        settings = options.connection.settings
        output = (
            "Database: "
            + settings.database
            + "\nHost: "
            + settings.host
            + "\nPort: "
            + settings.port
            + "\nUser: "
            + settings.user
        )
        return _success(buffer, output, False)
    if isinstance(command, MetaCommand_Connect):
        return Err(error=ClientError_QueryFailed(message="connecting to " + command.database + " requires an unavailable network host binding"))
    if isinstance(command, MetaCommand_RefreshCatalog):
        return Err(error=ClientError_CatalogFailed(message="catalog refresh requires an unavailable database.read host binding"))
    if isinstance(command, MetaCommand_Copy):
        if command.from_file:
            return Err(error=ClientError_ImportFailed(path=command.path, message="database import requires an unavailable database.write host binding"))
        return Err(error=ClientError_ExportFailed(path=command.path, message="database export requires an unavailable database.read host binding"))
    if isinstance(command, MetaCommand_EditBuffer):
        return Err(error=ClientError_EditorFailed(message="external editor requires an unavailable file host binding"))
    if isinstance(command, MetaCommand_ReadFile):
        return Err(error=ClientError_ImportFailed(path=command.path, message="reading SQL requires an unavailable file.read host binding"))
    if isinstance(command, MetaCommand_ReadRelativeFile):
        return Err(error=ClientError_ImportFailed(path=command.path, message="reading SQL requires an unavailable file.read host binding"))
    if isinstance(command, MetaCommand_WriteBuffer):
        return Err(error=ClientError_ExportFailed(path=command.path, message="writing SQL requires an unavailable file.write host binding"))
    if isinstance(command, MetaCommand_ExecuteBuffer):
        return Err(error=ClientError_QueryFailed(message="query execution requires an unavailable database host binding"))
    if isinstance(command, MetaCommand_ExecuteExpanded):
        return Err(error=ClientError_QueryFailed(message="query execution requires an unavailable database host binding"))
    if isinstance(command, MetaCommand_Watch):
        return Err(error=ClientError_QueryFailed(message="watching queries requires an unavailable database host binding"))
    if isinstance(command, MetaCommand_Password):
        return Err(error=ClientError_InvalidCommand(source="password changes require an unavailable terminal host binding"))
    if isinstance(command, MetaCommand_ListNotifications):
        return Err(error=ClientError_NotificationFailed(message="notifications require an unavailable database.read host binding"))
    if isinstance(command, MetaCommand_History):
        return Err(error=ClientError_HistoryFailed(path=options.history.path, message="history requires an unavailable file.read host binding"))
    if isinstance(command, MetaCommand_NamedQuery):
        return Err(error=ClientError_FavoriteFailed(name=command.name))
    if isinstance(command, MetaCommand_DeleteNamedQuery):
        return Err(error=ClientError_FavoriteFailed(name=command.name))
    if isinstance(command, MetaCommand_PrintNamedQuery):
        return Err(error=ClientError_FavoriteFailed(name=command.name))
    if isinstance(command, MetaCommand_SaveNamedQuery):
        return Err(error=ClientError_FavoriteFailed(name=command.name))
    if isinstance(command, MetaCommand_Favorite):
        return Err(error=ClientError_FavoriteFailed(name=command.name))
    if isinstance(command, MetaCommand_DeleteFavorite):
        return Err(error=ClientError_FavoriteFailed(name=command.name))
    if isinstance(command, MetaCommand_ListFavorites):
        return Err(error=ClientError_FavoriteFailed(name=command.pattern))

    lines: list[str] = []
    if isinstance(command, MetaCommand_ListDatabases):
        for database in catalog.databases:
            lines.append(database)
        return _success(buffer, "\n".join(lines), False)
    if isinstance(command, MetaCommand_ListSchemas):
        for schema in catalog.schemas:
            if _matches(schema, command.pattern):
                lines.append(schema)
        return _success(buffer, "\n".join(lines), False)
    if isinstance(command, MetaCommand_ListRoles):
        for role in catalog.roles:
            lines.append(role)
        return _success(buffer, "\n".join(lines), False)
    if isinstance(command, MetaCommand_ListExtensions):
        for extension in catalog.extensions:
            lines.append(extension)
        return _success(buffer, "\n".join(lines), False)
    if isinstance(command, MetaCommand_ListFunctions):
        for routine in catalog.routines:
            qualified = routine.schema + "." + routine.name
            if _matches(qualified, command.pattern):
                lines.append(qualified + "(" + routine.arguments + ") -> " + routine.result_type)
        return _success(buffer, "\n".join(lines), False)
    if isinstance(command, MetaCommand_ShowFunction):
        for routine in catalog.routines:
            qualified = routine.schema + "." + routine.name
            if _matches(qualified, command.pattern):
                lines.append(qualified + "(" + routine.arguments + ") -> " + routine.result_type)
        return _success(buffer, "\n".join(lines), False)
    if isinstance(command, MetaCommand_Describe):
        for relation in catalog.relations:
            qualified = relation.schema + "." + relation.name
            if _matches(qualified, command.pattern):
                lines.append(qualified + " [" + relation.kind + "]")
                for column in relation.columns:
                    lines.append("  " + column.name)
        return _success(buffer, "\n".join(lines), False)

    pattern = ""
    kind = ""
    if isinstance(command, MetaCommand_ListTables):
        pattern = command.pattern
        kind = "table"
    elif isinstance(command, MetaCommand_ListViews):
        pattern = command.pattern
        kind = "view"
    elif isinstance(command, MetaCommand_ListForeignTables):
        pattern = command.pattern
        kind = "foreign table"
    elif isinstance(command, MetaCommand_ListIndexes):
        pattern = command.pattern
        kind = "index"
    elif isinstance(command, MetaCommand_ListMaterializedViews):
        pattern = command.pattern
        kind = "materialized view"
    elif isinstance(command, MetaCommand_ListSequences):
        pattern = command.pattern
        kind = "sequence"
    elif isinstance(command, MetaCommand_ListDomains):
        pattern = command.pattern
        kind = "domain"
    elif isinstance(command, MetaCommand_ListDataTypes):
        pattern = command.pattern
        kind = "type"
    if kind != "":
        for relation in catalog.relations:
            qualified = relation.schema + "." + relation.name
            if relation.kind.casefold() == kind and _matches(qualified, pattern):
                lines.append(qualified)
        return _success(buffer, "\n".join(lines), False)

    if isinstance(command, MetaCommand_ListTextSearchConfigurations):
        return _success(buffer, "", False)
    if isinstance(command, MetaCommand_ListTablespaces):
        return _success(buffer, "", False)
    if isinstance(command, MetaCommand_ListDefaultPrivileges):
        return _success(buffer, "", False)
    if isinstance(command, MetaCommand_ListPrivileges):
        return _success(buffer, "", False)

    return Err(error=ClientError_InvalidCommand(source="unsupported meta command"))
