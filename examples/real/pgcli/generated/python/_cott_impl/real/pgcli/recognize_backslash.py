from real.pgcli import parse_meta_command
from real.pgcli_types import (
    BackslashCommand,
    BackslashCommand_Describe,
    BackslashCommand_Help,
    BackslashCommand_Quit,
    BackslashCommand_Tables,
    BackslashCommand_Unknown,
    MetaCommand_Describe,
    MetaCommand_Help,
    MetaCommand_ListTables,
    MetaCommand_Quit,
)


def recognize_backslash(source: str) -> BackslashCommand:
    command = parse_meta_command(source)
    if isinstance(command, MetaCommand_Quit):
        return BackslashCommand_Quit()
    if isinstance(command, MetaCommand_Help):
        return BackslashCommand_Help()
    if isinstance(command, MetaCommand_ListTables):
        return BackslashCommand_Tables()
    if isinstance(command, MetaCommand_Describe):
        return BackslashCommand_Describe()
    return BackslashCommand_Unknown()
