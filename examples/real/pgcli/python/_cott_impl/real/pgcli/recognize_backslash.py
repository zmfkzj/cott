from real.pgcli_types import (
    BackslashCommand,
    BackslashCommand_Describe,
    BackslashCommand_Help,
    BackslashCommand_Quit,
    BackslashCommand_Tables,
    BackslashCommand_Unknown,
)


def recognize_backslash(source: str) -> BackslashCommand:
    value = source.strip()
    if not value.startswith("\\"):
        return BackslashCommand_Unknown()

    body = value[1:]
    index = 0
    while index < len(body) and not body[index].isspace():
        index += 1
    command = body[:index]
    if command.endswith("+"):
        command = command[:-1]

    if command == "q":
        return BackslashCommand_Quit()
    if command == "?":
        return BackslashCommand_Help()
    if command == "dt":
        return BackslashCommand_Tables()
    if command == "d":
        return BackslashCommand_Describe()
    return BackslashCommand_Unknown()
