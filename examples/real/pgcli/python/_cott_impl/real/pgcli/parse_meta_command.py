from pathlib import Path

from cott_runtime import CottList
from real.pgcli_types import (
    MetaCommand,
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
    TableFormat_Aligned,
    TableFormat_Csv,
    TableFormat_Html,
    TableFormat_Json,
    TableFormat_JsonLines,
    TableFormat_Latex,
    TableFormat_Markdown,
    TableFormat_Tsv,
    TableFormat_Vertical,
)


def _split_head(value: str) -> tuple[str, str]:
    index = 0
    while index < len(value) and not value[index].isspace():
        index += 1
    command = value[:index]
    while index < len(value) and value[index].isspace():
        index += 1
    return (command, value[index:].strip())


def _split_pair(value: str) -> tuple[str, str]:
    first, remainder = _split_head(value)
    return (first, remainder)


def _format_command(value: str, source: str) -> MetaCommand:
    folded = value.casefold()
    if folded == "aligned" or folded == "psql":
        return MetaCommand_SetFormat(format=TableFormat_Aligned())
    if folded == "csv":
        return MetaCommand_SetFormat(format=TableFormat_Csv())
    if folded == "tsv":
        return MetaCommand_SetFormat(format=TableFormat_Tsv())
    if folded == "json":
        return MetaCommand_SetFormat(format=TableFormat_Json())
    if folded == "jsonlines" or folded == "jsonl" or folded == "ndjson":
        return MetaCommand_SetFormat(format=TableFormat_JsonLines())
    if folded == "html":
        return MetaCommand_SetFormat(format=TableFormat_Html())
    if folded == "latex":
        return MetaCommand_SetFormat(format=TableFormat_Latex())
    if folded == "markdown" or folded == "md":
        return MetaCommand_SetFormat(format=TableFormat_Markdown())
    if folded == "vertical":
        return MetaCommand_SetFormat(format=TableFormat_Vertical())
    return MetaCommand_Unknown(source=source)


def _copy_command(value: str, source: str) -> MetaCommand:
    table, remainder = _split_head(value)
    direction, path = _split_head(remainder)
    if table == "" or path == "":
        return MetaCommand_Unknown(source=source)
    folded = direction.casefold()
    if folded == "from":
        return MetaCommand_Copy(table=table, path=Path(path), from_file=True)
    if folded == "to":
        return MetaCommand_Copy(table=table, path=Path(path), from_file=False)
    return MetaCommand_Unknown(source=source)


def _named_query_command(value: str) -> MetaCommand:
    words = value.split()
    if len(words) == 0:
        return MetaCommand_NamedQuery(name="", arguments=CottList(values=[]))
    return MetaCommand_NamedQuery(name=words[0], arguments=CottList(values=words[1:]))


def _save_named_query_command(value: str, source: str) -> MetaCommand:
    name, sql = _split_pair(value)
    if name == "" or sql == "":
        return MetaCommand_Unknown(source=source)
    return MetaCommand_SaveNamedQuery(name=name, sql=sql)


def _enabled(value: str) -> bool:
    folded = value.casefold()
    return folded != "off" and folded != "false" and folded != "0"


def _watch_milliseconds(value: str) -> int:
    if value == "":
        return 2000
    text = value
    if text.casefold().startswith("sec="):
        text = text[4:]
    if text == "":
        return -1
    whole = 0
    fraction = 0
    fraction_digits = 0
    decimal = False
    for character in text:
        if character == "." and not decimal:
            decimal = True
        elif "0" <= character <= "9":
            digit = ord(character) - ord("0")
            if decimal:
                if fraction_digits < 3:
                    fraction = fraction * 10 + digit
                    fraction_digits += 1
                elif digit != 0:
                    return -1
            else:
                whole = whole * 10 + digit
                if whole > 4294967:
                    return -1
        else:
            return -1
    if decimal and fraction_digits == 0:
        return -1
    while fraction_digits < 3:
        fraction *= 10
        fraction_digits += 1
    milliseconds = whole * 1000 + fraction
    if milliseconds <= 0 or milliseconds > 4294967295:
        return -1
    return milliseconds


def parse_meta_command(source: str) -> MetaCommand:
    value = source.strip()
    if value.casefold() == "quit":
        return MetaCommand_Quit()
    if not value.startswith("\\"):
        return MetaCommand_Unknown(source=source)

    body = value[1:]
    if body.startswith("!"):
        return MetaCommand_Shell(command=body[1:].strip())
    command, argument = _split_head(body)
    plain_command = command[:-1] if command.endswith("+") else command

    if plain_command == "q":
        return MetaCommand_Quit()
    if plain_command == "#" or plain_command == "refresh":
        return MetaCommand_RefreshCatalog()
    if plain_command == "?":
        return MetaCommand_Help()
    if plain_command == "h":
        return MetaCommand_SqlHelp(topic=argument)
    if plain_command == "T":
        return _format_command(argument, source)
    if plain_command == "c" or plain_command == "connect":
        return MetaCommand_Connect(database=argument)
    if plain_command == "conninfo":
        return MetaCommand_ConnectionInfo()
    if plain_command == "copy":
        return _copy_command(argument, source)
    if plain_command == "d":
        return MetaCommand_Describe(pattern=argument)
    if plain_command == "dD":
        return MetaCommand_ListDomains(pattern=argument)
    if plain_command == "dE" or plain_command == "det":
        return MetaCommand_ListForeignTables(pattern=argument)
    if plain_command == "dF":
        return MetaCommand_ListTextSearchConfigurations(pattern=argument)
    if plain_command == "dT" or plain_command == "dTS":
        return MetaCommand_ListDataTypes(pattern=argument)
    if plain_command == "db":
        return MetaCommand_ListTablespaces(pattern=argument)
    if plain_command == "ddp":
        return MetaCommand_ListDefaultPrivileges(pattern=argument)
    if plain_command == "df":
        return MetaCommand_ListFunctions(pattern=argument)
    if plain_command == "di":
        return MetaCommand_ListIndexes(pattern=argument)
    if plain_command == "dm":
        return MetaCommand_ListMaterializedViews(pattern=argument)
    if plain_command == "dn":
        return MetaCommand_ListSchemas(pattern=argument)
    if plain_command == "dp" or plain_command == "z":
        return MetaCommand_ListPrivileges(pattern=argument)
    if plain_command == "ds":
        return MetaCommand_ListSequences(pattern=argument)
    if plain_command == "dt":
        return MetaCommand_ListTables(pattern=argument)
    if plain_command == "du" or plain_command == "dg":
        return MetaCommand_ListRoles()
    if plain_command == "dv":
        return MetaCommand_ListViews(pattern=argument)
    if plain_command == "dx":
        return MetaCommand_ListExtensions()
    if plain_command == "l" or plain_command == "list":
        return MetaCommand_ListDatabases()
    if plain_command == "sf":
        return MetaCommand_ShowFunction(pattern=argument)
    if plain_command == "e":
        return MetaCommand_EditBuffer()
    if plain_command == "echo":
        return MetaCommand_Echo(text=argument)
    if plain_command == "i":
        if argument == "":
            return MetaCommand_Unknown(source=source)
        return MetaCommand_ReadFile(path=Path(argument))
    if plain_command == "ir":
        if argument == "":
            return MetaCommand_Unknown(source=source)
        return MetaCommand_ReadRelativeFile(path=Path(argument))
    if plain_command == "n":
        return _named_query_command(argument)
    if plain_command == "log-file" or plain_command == "L":
        return MetaCommand_SetLogFile(path=Path(argument))
    if plain_command == "nd":
        return MetaCommand_DeleteNamedQuery(name=argument)
    if plain_command == "np":
        return MetaCommand_PrintNamedQuery(name=argument)
    if plain_command == "ns":
        return _save_named_query_command(argument, source)
    if plain_command == "o":
        if argument == "":
            return MetaCommand_ClearOutput()
        return MetaCommand_SetOutput(path=Path(argument))
    if plain_command == "pager":
        return MetaCommand_SetPager(enabled=_enabled(argument))
    if plain_command == "pset":
        key, option_value = _split_pair(argument)
        return MetaCommand_SetOptions(key=key, value=option_value)
    if plain_command == "qecho":
        return MetaCommand_QueryOutputEcho(text=argument)
    if plain_command == "timing":
        return MetaCommand_Timing()
    if plain_command == "v":
        return MetaCommand_VerboseErrors(enabled=_enabled(argument))
    if plain_command == "watch":
        interval_ms = _watch_milliseconds(argument)
        if interval_ms < 0:
            return MetaCommand_Unknown(source=source)
        return MetaCommand_Watch(interval_ms=interval_ms)
    if plain_command == "x":
        return MetaCommand_Expanded()
    if plain_command == "g":
        return MetaCommand_ExecuteBuffer()
    if plain_command == "gx":
        return MetaCommand_ExecuteExpanded()
    if plain_command == "p":
        return MetaCommand_PrintBuffer()
    if plain_command == "r":
        return MetaCommand_ResetBuffer()
    if plain_command == "w":
        if argument == "":
            return MetaCommand_Unknown(source=source)
        return MetaCommand_WriteBuffer(path=Path(argument))
    if plain_command == "s":
        return MetaCommand_History(pattern=argument)
    if plain_command == "f":
        return MetaCommand_Favorite(name=argument)
    if plain_command == "fl" or plain_command == "favorites":
        return MetaCommand_ListFavorites(pattern=argument)
    if plain_command == "fd":
        return MetaCommand_DeleteFavorite(name=argument)
    if plain_command == "password":
        return MetaCommand_Password()
    if plain_command == "notify" or plain_command == "notifications":
        return MetaCommand_ListNotifications()
    return MetaCommand_Unknown(source=source)
