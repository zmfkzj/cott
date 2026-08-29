from real.pgcli_types import BackslashCommand, BackslashCommand_Describe, BackslashCommand_Help, BackslashCommand_Quit, BackslashCommand_Tables, BackslashCommand_Unknown


def recognize_backslash(source: str) -> BackslashCommand:
    tokens = source.strip().split()
    if not tokens:
        return BackslashCommand_Unknown()

    command = tokens[0]
    if command == "\\q":
        return BackslashCommand_Quit()
    if command == "\\?":
        return BackslashCommand_Help()
    if command == "\\dt":
        return BackslashCommand_Tables()
    if command == "\\d":
        return BackslashCommand_Describe()
    return BackslashCommand_Unknown()
