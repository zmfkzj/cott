from cott_runtime import CottList, Err, Ok, Result
from real.toolong import filter_entries, load_entries, parse_arguments, render_entries
from real.toolong_types import ToolongError


def execute(arguments: CottList[str]) -> Result[str, ToolongError]:
    match parse_arguments(arguments):
        case Ok(value=options):
            match load_entries(options.sources):
                case Ok(value=entries):
                    filtered = filter_entries(entries, options.contains)
                    return Ok(value=render_entries(filtered))
                case Err(error=error):
                    return Err(error=error)
        case Err(error=error):
            return Err(error=error)
