import click


def help_text(program: str) -> str:
    command = click.Command(
        name=program,
        help="View / tail / search log files.",
        params=[
            click.Option(["--version"], is_flag=True, expose_value=False, is_eager=True, help="Show the version and exit."),
            click.Argument(["files"], metavar="FILE1 FILE2", nargs=-1),
            click.Option(["-m", "--merge"], is_flag=True, help="Merge files."),
            click.Option(["-o", "--output-merge"], metavar="PATH", type=click.Path(), help="Path to save merged file (requires -m)."),
        ],
    )
    ctx = click.Context(command, info_name=program, terminal_width=80)
    return command.get_help(ctx).rstrip("\n")
