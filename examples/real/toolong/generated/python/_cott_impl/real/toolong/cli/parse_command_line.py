from click import Option as ClickOption
from click.exceptions import BadOptionUsage, NoSuchOption
from click.parser import OptionParser

from cott_runtime import CottList, Nothing, Some
from real.toolong.cli import help_text
from real.toolong.cli_types import CommandLine, CommandLine_Run, CommandLine_ShowHelp, CommandLine_ShowVersion, CommandLine_UsageError


def parse_command_line(arguments: CottList[str], program: str) -> CommandLine:
    parser = OptionParser()
    parser.add_option(ClickOption(["--version"], is_flag=True), ["--version"], dest="version", action="store_const", const=True)
    parser.add_option(ClickOption(["-m", "--merge"], is_flag=True), ["-m", "--merge"], dest="merge", action="store_const", const=True)
    parser.add_option(ClickOption(["-o", "--output-merge"]), ["-o", "--output-merge"], dest="output_merge", action="store")
    parser.add_option(ClickOption(["--help"], is_flag=True), ["--help"], dest="help", action="store_const", const=True)
    args: list[str] = []
    for argument in arguments:
        args.append(argument)
    try:
        opts, files, _order = parser.parse_args(args)
    except NoSuchOption as error:
        return CommandLine_UsageError(output=f"Usage: {program} [OPTIONS] FILE1 FILE2\nTry '{program} --help' for help.\n\nError: {error.format_message()}")
    except BadOptionUsage as error:
        return CommandLine_UsageError(output=f"Error: {error.format_message()}")
    if opts.get("version"):
        return CommandLine_ShowVersion(output=f"{program}, version 1.4.0")
    if opts.get("help"):
        return CommandLine_ShowHelp(output=help_text(program))
    output: object = opts.get("output_merge")
    file_values: list[str] = [str(item) for item in files]
    if isinstance(output, str):
        return CommandLine_Run(files=CottList(values=file_values), merge=bool(opts.get("merge")), output_merge=Some(value=output))
    else:
        return CommandLine_Run(files=CottList(values=file_values), merge=bool(opts.get("merge")), output_merge=Nothing())
