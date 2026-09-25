from pathlib import Path

from cott_runtime import CottList
from real.pgcli_types import (
    MetaCommand,
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
    MetaCommand_ListDataTypes,
    MetaCommand_ListDatabases,
    MetaCommand_ListDefaultPrivileges,
    MetaCommand_ListDomains,
    MetaCommand_ListExtensions,
    MetaCommand_ListFavorites,
    MetaCommand_ListForeignTables,
    MetaCommand_ListFunctions,
    MetaCommand_ListIndexes,
    MetaCommand_ListMaterializedViews,
    MetaCommand_ListPrivileges,
    MetaCommand_ListRoles,
    MetaCommand_ListSchemas,
    MetaCommand_ListSequences,
    MetaCommand_ListTables,
    MetaCommand_ListTablespaces,
    MetaCommand_ListTextSearchConfigurations,
    MetaCommand_ListViews,
    MetaCommand_NamedQuery,
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
    MetaCommand_SetPager,
    MetaCommand_ShowFunction,
    MetaCommand_SqlHelp,
    MetaCommand_Timing,
    MetaCommand_Unknown,
    MetaCommand_WriteBuffer,
    TableFormat,
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


def _ascii_lower(text: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)


def _format(name: str) -> TableFormat | None:
    key = _ascii_lower(name)
    if key == "aligned":
        return TableFormat_Aligned()
    if key == "csv":
        return TableFormat_Csv()
    if key == "tsv":
        return TableFormat_Tsv()
    if key == "json":
        return TableFormat_Json()
    if key == "jsonl":
        return TableFormat_JsonLines()
    if key == "html":
        return TableFormat_Html()
    if key == "latex":
        return TableFormat_Latex()
    if key == "markdown":
        return TableFormat_Markdown()
    if key == "vertical":
        return TableFormat_Vertical()
    return None


def _unquote(text: str) -> str:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    return text


def _single_word(arg: str) -> bool:
    return bool(arg) and len(arg.split()) == 1


def _no_arg_command(cmd: str) -> MetaCommand | None:
    if cmd in ("\\q", "\\quit", "quit", "exit"):
        return MetaCommand_Quit()
    if cmd in ("\\#", "\\refresh"):
        return MetaCommand_RefreshCatalog()
    if cmd in ("\\?", "help"):
        return MetaCommand_Help()
    if cmd == "\\conninfo":
        return MetaCommand_ConnectionInfo()
    if cmd in ("\\du", "\\dg"):
        return MetaCommand_ListRoles()
    if cmd == "\\dx":
        return MetaCommand_ListExtensions()
    if cmd in ("\\l", "\\list"):
        return MetaCommand_ListDatabases()
    if cmd == "\\e":
        return MetaCommand_EditBuffer()
    if cmd == "\\timing":
        return MetaCommand_Timing()
    if cmd == "\\x":
        return MetaCommand_Expanded()
    if cmd == "\\g":
        return MetaCommand_ExecuteBuffer()
    if cmd == "\\G":
        return MetaCommand_ExecuteExpanded()
    if cmd == "\\p":
        return MetaCommand_PrintBuffer()
    if cmd == "\\r":
        return MetaCommand_ResetBuffer()
    return None


def _pattern_command(cmd: str, arg: str) -> MetaCommand | None:
    if cmd == "\\d":
        return MetaCommand_Describe(pattern=arg)
    if cmd == "\\dD":
        return MetaCommand_ListDomains(pattern=arg)
    if cmd == "\\dE":
        return MetaCommand_ListForeignTables(pattern=arg)
    if cmd == "\\dF":
        return MetaCommand_ListTextSearchConfigurations(pattern=arg)
    if cmd == "\\dT":
        return MetaCommand_ListDataTypes(pattern=arg)
    if cmd == "\\db":
        return MetaCommand_ListTablespaces(pattern=arg)
    if cmd == "\\ddp":
        return MetaCommand_ListDefaultPrivileges(pattern=arg)
    if cmd == "\\df":
        return MetaCommand_ListFunctions(pattern=arg)
    if cmd == "\\di":
        return MetaCommand_ListIndexes(pattern=arg)
    if cmd == "\\dm":
        return MetaCommand_ListMaterializedViews(pattern=arg)
    if cmd == "\\dn":
        return MetaCommand_ListSchemas(pattern=arg)
    if cmd in ("\\dp", "\\z"):
        return MetaCommand_ListPrivileges(pattern=arg)
    if cmd == "\\ds":
        return MetaCommand_ListSequences(pattern=arg)
    if cmd == "\\dt":
        return MetaCommand_ListTables(pattern=arg)
    if cmd == "\\dv":
        return MetaCommand_ListViews(pattern=arg)
    if cmd == "\\s":
        return MetaCommand_History(pattern=arg)
    if cmd == "\\fl":
        return MetaCommand_ListFavorites(pattern=arg)
    return None


def _word_command(cmd: str, arg: str) -> MetaCommand | None:
    if cmd == "\\sf":
        return MetaCommand_ShowFunction(pattern=arg)
    if cmd in ("\\c", "\\connect"):
        return MetaCommand_Connect(database=arg)
    if cmd == "\\nd":
        return MetaCommand_DeleteNamedQuery(name=arg)
    if cmd == "\\np":
        return MetaCommand_PrintNamedQuery(name=arg)
    if cmd == "\\fd":
        return MetaCommand_DeleteFavorite(name=arg)
    return None


def _path_command(cmd: str, path: Path) -> MetaCommand | None:
    if cmd == "\\i":
        return MetaCommand_ReadFile(path=path)
    if cmd == "\\ir":
        return MetaCommand_ReadRelativeFile(path=path)
    if cmd == "\\w":
        return MetaCommand_WriteBuffer(path=path)
    return None


def _parse_copy(source: str, arg: str) -> MetaCommand:
    parts = arg.split(None, 2)
    if len(parts) != 3:
        return MetaCommand_Unknown(source=source)
    direction = _ascii_lower(parts[1])
    if direction not in ("from", "to"):
        return MetaCommand_Unknown(source=source)
    target = _unquote(parts[2].strip())
    if not target:
        return MetaCommand_Unknown(source=source)
    return MetaCommand_Copy(table=parts[0], path=Path(target), from_file=direction == "from")


def _other_command(source: str, cmd: str, arg: str) -> MetaCommand:
    if cmd == "\\h":
        return MetaCommand_SqlHelp(topic=arg) if arg else MetaCommand_Help()
    if cmd == "\\echo":
        return MetaCommand_Echo(text=arg)
    if cmd == "\\qecho":
        return MetaCommand_QueryOutputEcho(text=arg)
    if cmd == "\\f":
        return MetaCommand_Favorite(name=arg) if arg else MetaCommand_ListFavorites(pattern="")
    if cmd == "\\T":
        fmt = _format(arg)
        return MetaCommand_SetFormat(format=fmt) if fmt is not None else MetaCommand_Unknown(source=source)
    if cmd == "\\pager":
        if arg == "on":
            return MetaCommand_SetPager(enabled=True)
        if arg == "off":
            return MetaCommand_SetPager(enabled=False)
        return MetaCommand_Unknown(source=source)
    if cmd == "\\n":
        words = arg.split()
        if not words:
            return MetaCommand_Unknown(source=source)
        return MetaCommand_NamedQuery(name=words[0], arguments=CottList(values=words[1:]))
    if cmd == "\\ns":
        pieces = arg.split(None, 1)
        if len(pieces) != 2 or not pieces[1].strip():
            return MetaCommand_Unknown(source=source)
        return MetaCommand_SaveNamedQuery(name=pieces[0], sql=pieces[1].strip())
    if cmd == "\\copy":
        return _parse_copy(source, arg)
    return MetaCommand_Unknown(source=source)


def parse_meta_command(source: str) -> MetaCommand:
    text = source.strip()
    if text.endswith(";"):
        text = text[:-1].strip()
    if not text:
        return MetaCommand_Unknown(source=source)
    parts = text.split(None, 1)
    head = parts[0]
    arg = parts[1].strip() if len(parts) == 2 else ""
    cmd = head[:-1] if len(head) > 2 and head.endswith("+") else head
    simple = _no_arg_command(cmd)
    if simple is not None:
        return simple if not arg else MetaCommand_Unknown(source=source)
    listed = _pattern_command(cmd, arg)
    if listed is not None:
        return listed
    if cmd in ("\\sf", "\\c", "\\connect", "\\nd", "\\np", "\\fd"):
        worded = _word_command(cmd, arg) if _single_word(arg) else None
        return worded if worded is not None else MetaCommand_Unknown(source=source)
    if cmd in ("\\i", "\\ir", "\\w"):
        target = _unquote(arg)
        pathed = _path_command(cmd, Path(target)) if target else None
        return pathed if pathed is not None else MetaCommand_Unknown(source=source)
    return _other_command(source, cmd, arg)
