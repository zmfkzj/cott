import os
import pathlib
from typing import Any, Callable, Literal, cast

from configobj import ConfigObj
from cott_runtime import CottContractViolation, Err, Ok, Opaque, Result, _cott_fixture_read
from pgspecial.main import NO_QUERY, PARSED_QUERY, PGSpecial
from pgspecial.namedqueries import NamedQueries

from real.pgcli.session_types import EvaluateError, EvaluateError_Failed, SpecialSetup


def create_special_handle(setup: SpecialSetup) -> Result[Opaque[Literal["pgcli.pgspecial"]], EvaluateError]:
    try:
        special: Any = PGSpecial()
        special.timing_enabled = setup.timing
        special.pset_pager("on" if setup.enable_pager else "off")

        path = pathlib.Path(os.path.expanduser(str(setup.config_path)))
        try:
            contents = _cott_fixture_read(path)
        except CottContractViolation as error:
            if error.message == "fixture adapters are inactive":
                config: Any = ConfigObj(str(path), interpolation=False, encoding="utf-8")
            elif isinstance(error.__cause__, FileNotFoundError):
                config = ConfigObj([], interpolation=False, encoding="utf-8")
                config.filename = str(path)
            elif isinstance(error.__cause__, OSError):
                raise error.__cause__
            else:
                raise
        else:
            config = ConfigObj(contents.decode("utf-8").splitlines(keepends=True), interpolation=False, encoding="utf-8")
            config.filename = str(path)

        named: Any = NamedQueries
        named.instance = named.from_config(config)
        no_query = cast(object, NO_QUERY)
        parsed_query = cast(object, PARSED_QUERY)
        commands: tuple[tuple[str, str, str, object, bool, tuple[str, ...]], ...] = (
            ("\\nq", "\\nq", "Toggle named query quiet mode (hide query text)", no_query, True, ()),
            ("\\ne", "\\ne name", "Edit a named query in the external editor.", parsed_query, True, ()),
            ("\\c", "\\c[onnect] database_name", "Change to a new database.", parsed_query, True, ("use", "\\connect", "USE")),
            ("\\q", "\\q", "Quit pgcli.", no_query, True, (":q",)),
            ("quit", "quit", "Quit pgcli.", no_query, False, ("exit",)),
            ("\\#", "\\#", "Refresh auto-completions.", no_query, True, ()),
            ("\\refresh", "\\refresh", "Refresh auto-completions.", no_query, True, ()),
            ("\\i", "\\i filename", "Execute commands from file.", parsed_query, True, ()),
            ("\\o", "\\o [filename]", "Send all query results to file.", parsed_query, True, ()),
            ("\\log-file", "\\log-file [filename]", "Log all query results to a logfile, in addition to the normal output destination.", parsed_query, True, ()),
            ("\\conninfo", "\\conninfo", "Get connection details", parsed_query, True, ()),
            ("\\T", "\\T [format]", "Change the table format used to output results", parsed_query, True, ()),
            ("\\echo", "\\echo [string]", "Echo a string to stdout", parsed_query, True, ()),
            ("\\qecho", "\\qecho [string]", "Echo a string to the query output channel.", parsed_query, True, ()),
            ("\\v", "\\v [on|off]", "Toggle verbose errors.", parsed_query, True, ()),
        )
        for command, syntax, description, arg_type, case_sensitive, aliases in commands:
            handler: Callable[..., list[object]] = lambda *args, **kwargs: []
            special.register(handler, command, syntax, description, arg_type=arg_type, case_sensitive=case_sensitive, aliases=aliases)
        return Ok(value=Opaque(tag="pgcli.pgspecial", value=special))
    except Exception as error:
        return Err[EvaluateError](error=EvaluateError_Failed(message=str(error)))
