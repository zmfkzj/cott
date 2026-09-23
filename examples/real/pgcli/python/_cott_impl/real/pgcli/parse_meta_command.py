from pathlib import Path
from typing import Final

from cott_runtime import CottList
from real.pgcli_types import MetaCommand, MetaCommand_ClearOutput, MetaCommand_Connect, MetaCommand_ConnectionInfo, MetaCommand_Copy, MetaCommand_DeleteFavorite, MetaCommand_DeleteNamedQuery, MetaCommand_Describe, MetaCommand_Echo, MetaCommand_EditBuffer, MetaCommand_ExecuteBuffer, MetaCommand_ExecuteExpanded, MetaCommand_Expanded, MetaCommand_Favorite, MetaCommand_Help, MetaCommand_History, MetaCommand_ListDataTypes, MetaCommand_ListDatabases, MetaCommand_ListDefaultPrivileges, MetaCommand_ListDomains, MetaCommand_ListExtensions, MetaCommand_ListFavorites, MetaCommand_ListForeignTables, MetaCommand_ListFunctions, MetaCommand_ListIndexes, MetaCommand_ListMaterializedViews, MetaCommand_ListNotifications, MetaCommand_ListPrivileges, MetaCommand_ListRoles, MetaCommand_ListSchemas, MetaCommand_ListSequences, MetaCommand_ListTables, MetaCommand_ListTablespaces, MetaCommand_ListTextSearchConfigurations, MetaCommand_ListViews, MetaCommand_NamedQuery, MetaCommand_Password, MetaCommand_PrintBuffer, MetaCommand_PrintNamedQuery, MetaCommand_QueryOutputEcho, MetaCommand_Quit, MetaCommand_ReadFile, MetaCommand_ReadRelativeFile, MetaCommand_RefreshCatalog, MetaCommand_ResetBuffer, MetaCommand_SaveNamedQuery, MetaCommand_SetFormat, MetaCommand_SetLogFile, MetaCommand_SetOptions, MetaCommand_SetOutput, MetaCommand_SetPager, MetaCommand_Shell, MetaCommand_ShowFunction, MetaCommand_SqlHelp, MetaCommand_Timing, MetaCommand_Unknown, MetaCommand_VerboseErrors, MetaCommand_Watch, MetaCommand_WriteBuffer, TableFormat, TableFormat_Aligned, TableFormat_Csv, TableFormat_Html, TableFormat_Json, TableFormat_JsonLines, TableFormat_Latex, TableFormat_Markdown, TableFormat_Tsv, TableFormat_Vertical

_U32_MAX: Final[int] = 4294967295


def _format(name: str) -> TableFormat | None:
    key = name.lower()
    if key in ("aligned", "psql", "table", "fancy_grid", "grid"):
        return TableFormat_Aligned()
    if key == "csv":
        return TableFormat_Csv()
    if key == "tsv":
        return TableFormat_Tsv()
    if key == "json":
        return TableFormat_Json()
    if key in ("jsonl", "jsonlines", "json_lines"):
        return TableFormat_JsonLines()
    if key == "html":
        return TableFormat_Html()
    if key in ("latex", "latex_booktabs"):
        return TableFormat_Latex()
    if key in ("markdown", "md", "pipe", "github"):
        return TableFormat_Markdown()
    if key in ("vertical", "expanded"):
        return TableFormat_Vertical()
    return None


def _unquote(text: str) -> str:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    return text


def _bool_arg(arg: str) -> bool | None:
    key = arg.lower()
    if key in ("on", "true", "1", "yes"):
        return True
    if key in ("off", "false", "0", "no"):
        return False
    return None


def _parse_copy(source: str, arg: str) -> MetaCommand:
    parts = arg.split(None, 2)
    if len(parts) != 3:
        return MetaCommand_Unknown(source=source)
    direction = parts[1].lower()
    if direction not in ("from", "to"):
        return MetaCommand_Unknown(source=source)
    target = _unquote(parts[2].strip())
    if not parts[0] or not target:
        return MetaCommand_Unknown(source=source)
    return MetaCommand_Copy(table=parts[0], path=Path(target), from_file=direction == "from")


def _parse_watch(source: str, arg: str) -> MetaCommand:
    if not arg:
        return MetaCommand_Watch(interval_ms=2000)
    try:
        seconds = float(arg)
    except ValueError:
        return MetaCommand_Unknown(source=source)
    if not seconds > 0.0:
        return MetaCommand_Unknown(source=source)
    ms = round(seconds * 1000.0)
    if ms < 1 or ms > _U32_MAX:
        return MetaCommand_Unknown(source=source)
    return MetaCommand_Watch(interval_ms=ms)


def _pattern_command(source: str, cmd: str, arg: str) -> MetaCommand | None:
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
    if cmd == "\\sf":
        return MetaCommand_ShowFunction(pattern=arg) if arg else MetaCommand_Unknown(source=source)
    if cmd == "\\s":
        return MetaCommand_History(pattern=arg)
    if cmd == "\\fl":
        return MetaCommand_ListFavorites(pattern=arg)
    return None


def _no_arg_command(cmd: str) -> MetaCommand | None:
    if cmd in ("\\q", "\\quit", "quit", "exit", ":q"):
        return MetaCommand_Quit()
    if cmd in ("\\#", "\\refresh"):
        return MetaCommand_RefreshCatalog()
    if cmd in ("\\?", "help"):
        return MetaCommand_Help()
    if cmd in ("\\conninfo", "\\connectioninfo"):
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
    if cmd == "\\password":
        return MetaCommand_Password()
    if cmd in ("\\listen", "\\notifications"):
        return MetaCommand_ListNotifications()
    return None


def _arg_command(source: str, cmd: str, arg: str) -> MetaCommand:
    if cmd == "\\h":
        return MetaCommand_SqlHelp(topic=arg) if arg else MetaCommand_Help()
    if cmd == "\\!":
        return MetaCommand_Shell(command=arg) if arg else MetaCommand_Unknown(source=source)
    if cmd == "\\T":
        fmt = _format(arg)
        if fmt is not None:
            return MetaCommand_SetFormat(format=fmt)
        return MetaCommand_Unknown(source=source)
    if cmd in ("\\c", "\\connect"):
        return MetaCommand_Connect(database=arg) if arg else MetaCommand_Unknown(source=source)
    if cmd == "\\copy":
        return _parse_copy(source, arg)
    if cmd == "\\echo":
        return MetaCommand_Echo(text=arg)
    if cmd == "\\qecho":
        return MetaCommand_QueryOutputEcho(text=arg)
    if cmd in ("\\i", "\\include"):
        return MetaCommand_ReadFile(path=Path(_unquote(arg))) if arg else MetaCommand_Unknown(source=source)
    if cmd in ("\\ir", "\\include_relative"):
        return MetaCommand_ReadRelativeFile(path=Path(_unquote(arg))) if arg else MetaCommand_Unknown(source=source)
    if cmd == "\\n":
        words = arg.split()
        if not words:
            return MetaCommand_Unknown(source=source)
        return MetaCommand_NamedQuery(name=words[0], arguments=CottList(values=words[1:]))
    if cmd == "\\log-file":
        return MetaCommand_SetLogFile(path=Path(_unquote(arg))) if arg else MetaCommand_Unknown(source=source)
    if cmd == "\\nd":
        return MetaCommand_DeleteNamedQuery(name=arg) if arg and " " not in arg else MetaCommand_Unknown(source=source)
    if cmd == "\\np":
        return MetaCommand_PrintNamedQuery(name=arg) if arg and " " not in arg else MetaCommand_Unknown(source=source)
    if cmd == "\\ns":
        pieces = arg.split(None, 1)
        if len(pieces) != 2:
            return MetaCommand_Unknown(source=source)
        return MetaCommand_SaveNamedQuery(name=pieces[0], sql=pieces[1].strip())
    if cmd in ("\\o", "\\out"):
        return MetaCommand_SetOutput(path=Path(_unquote(arg))) if arg else MetaCommand_ClearOutput()
    if cmd == "\\pager":
        enabled = _bool_arg(arg)
        return MetaCommand_SetPager(enabled=enabled) if enabled is not None else MetaCommand_Unknown(source=source)
    if cmd == "\\v":
        verbose = _bool_arg(arg) if arg else True
        return MetaCommand_VerboseErrors(enabled=verbose) if verbose is not None else MetaCommand_Unknown(source=source)
    if cmd == "\\set":
        kv = arg.split(None, 1)
        if not kv:
            return MetaCommand_Unknown(source=source)
        return MetaCommand_SetOptions(key=kv[0], value=kv[1].strip() if len(kv) == 2 else "")
    if cmd == "\\watch":
        return _parse_watch(source, arg)
    if cmd == "\\w":
        return MetaCommand_WriteBuffer(path=Path(_unquote(arg))) if arg else MetaCommand_Unknown(source=source)
    if cmd == "\\f":
        return MetaCommand_Favorite(name=arg) if arg else MetaCommand_ListFavorites(pattern="")
    if cmd == "\\fd":
        return MetaCommand_DeleteFavorite(name=arg) if arg else MetaCommand_Unknown(source=source)
    return MetaCommand_Unknown(source=source)


def parse_meta_command(source: str) -> MetaCommand:
    text = source.strip().rstrip(";").strip()
    if not text:
        return MetaCommand_Unknown(source=source)
    parts = text.split(None, 1)
    head = parts[0]
    arg = parts[1].strip() if len(parts) == 2 else ""
    cmd = head[:-1] if len(head) > 2 and head.endswith("+") else head
    simple = _no_arg_command(cmd)
    if simple is not None:
        return simple if not arg else MetaCommand_Unknown(source=source)
    listed = _pattern_command(source, cmd, arg)
    if listed is not None:
        return listed
    return _arg_command(source, cmd, arg)
