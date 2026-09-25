from cott_runtime import CottList, Err, Ok, Result
from real.toolong import filter_entries, load_entries, parse_arguments, render_entries
from real.toolong_types import LogEntry, ToolongError, ViewerOptions


def execute(arguments: CottList[str]) -> Result[str, ToolongError]:
    parsed: Result[ViewerOptions, ToolongError] = parse_arguments(arguments)
    if isinstance(parsed, Err):
        return parsed
    options: ViewerOptions = parsed.value
    loaded: Result[CottList[LogEntry], ToolongError] = load_entries(options.sources)
    if isinstance(loaded, Err):
        return loaded
    kept: CottList[LogEntry] = filter_entries(loaded.value, options.contains)
    return Ok(value=render_entries(kept))
