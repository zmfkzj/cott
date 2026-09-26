import re

from cott_runtime import CottList, Nothing, Some
from frogmouth.cli_types import COMMAND_LINE_HELP, COMMAND_LINE_USAGE, CommandLine, CommandLine_Browse, CommandLine_Invalid, CommandLine_ShowHelp, CommandLine_ShowVersion


def _is_option(argument: str) -> bool:
    if not argument.startswith("-") or len(argument) < 2 or " " in argument:
        return False
    return re.fullmatch(r"-\d+|-\d*\.\d+", argument) is None


def _asks_for(option: str, letter: str, name: str) -> bool:
    if option.startswith("--"):
        rest = option[2:]
        return rest != "" and name.startswith(rest)
    return option[1] == letter


def parse_command_line(arguments: CottList[str], textual_version: str) -> CommandLine:
    options: list[str] = []
    positionals: list[str] = []
    separated = False
    for argument in arguments:
        if separated:
            positionals.append(argument)
        elif argument == "--":
            separated = True
        elif _is_option(argument):
            options.append(argument)
        else:
            positionals.append(argument)
    for option in options:
        if _asks_for(option, "h", "help"):
            return CommandLine_ShowHelp(text=COMMAND_LINE_HELP)
        if _asks_for(option, "v", "version"):
            return CommandLine_ShowVersion(text=f"frogmouth 0.9.1 (Textual v{textual_version})")
    if options:
        return CommandLine_Invalid(message=COMMAND_LINE_USAGE + "\nfrogmouth: error: unrecognized arguments: " + " ".join(options))
    if positionals:
        return CommandLine_Browse(address=Some(value=" ".join(positionals)))
    return CommandLine_Browse(address=Nothing())
