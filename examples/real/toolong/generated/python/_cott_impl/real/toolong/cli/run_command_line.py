import os
import signal
import sys
import tempfile
from pathlib import Path

from cott_runtime import CottList, I32, Nothing, Option, Some
from real.toolong.cli import help_text, parse_command_line, plan_tabs
from real.toolong.cli_types import CommandLine_ShowHelp, CommandLine_ShowVersion, CommandLine_UsageError
from real.toolong.model_types import PipeFeed, TabPlan, ViewerSetup
from real.toolong.tui import run_viewer


def _write_interrupt() -> None:
    sys.stderr.write("^C")


def _run_setup(setup: ViewerSetup) -> None:
    try:
        run_viewer(setup)
    except Exception:
        return


def _close_descriptor(fd: int) -> None:
    try:
        os.close(fd)
    except OSError:
        return


def _run_piped() -> I32:
    signal.signal(signal.SIGINT, lambda signum, frame: _write_interrupt())
    signal.signal(signal.SIGTERM, lambda signum, frame: _write_interrupt())
    temp = tempfile.NamedTemporaryFile(mode="w+b", buffering=0, prefix="tl_")
    try:
        fd = os.dup(0)
        try:
            try:
                tty = os.open("/dev/tty", os.O_RDWR)
            except OSError as error:
                sys.stderr.write("Error: " + str(error))
                return 1
            try:
                os.dup2(tty, 0)
            finally:
                _close_descriptor(tty)
            path = Path(temp.name)
            tab = TabPlan(title=temp.name, paths=CottList(values=[path]), merged=False)
            setup = ViewerSetup(tabs=CottList(values=[tab]), save_merge=Nothing(), pipe=Some(value=PipeFeed(descriptor=fd, path=path)))
            _run_setup(setup)
        finally:
            _close_descriptor(fd)
    finally:
        temp.close()
    return 0


def run_command_line(arguments: CottList[str], program: str) -> I32:
    command = parse_command_line(arguments, program)
    if isinstance(command, CommandLine_ShowHelp):
        sys.stdout.write(command.output + "\n")
        return 0
    if isinstance(command, CommandLine_ShowVersion):
        sys.stdout.write(command.output + "\n")
        return 0
    if isinstance(command, CommandLine_UsageError):
        sys.stderr.write(command.output + "\n")
        return 2
    if not sys.stdin.isatty():
        return _run_piped()
    if len(command.files) == 0:
        sys.stdout.write(help_text(program) + "\n")
        return 0
    output = command.output_merge
    save: Option[Path]
    if isinstance(output, Some):
        save = Some(value=Path(output.value))
    else:
        save = Nothing()
    _run_setup(ViewerSetup(tabs=plan_tabs(command.files, command.merge), save_merge=save, pipe=Nothing()))
    return 0
