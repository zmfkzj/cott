from cott_runtime import Err, Ok, Result
from real.harlequin.core_types import QueryResult
from real.harlequin.render_types import (
    RenderError,
    RenderError_InvalidWidth,
    RenderError_UnsupportedCell,
    RenderLayout_Table,
    RenderLayout_Vertical,
    RenderOptions,
)


def render_result(result: QueryResult, options: RenderOptions) -> Result[str, RenderError]:
    if options.terminal_width == 0:
        return Err(error=RenderError_InvalidWidth(width=options.terminal_width))
    if options.maximum_cell_width == 0:
        return Err(error=RenderError_InvalidWidth(width=options.maximum_cell_width))

    rendered_result = str(result)
    if "\x00" in rendered_result:
        return Err(error=RenderError_UnsupportedCell(message="query result contains a NUL character"))

    width = min(options.terminal_width, options.maximum_cell_width)
    content = rendered_result[:width]
    match options.layout:
        case RenderLayout_Table():
            rendered = f"Result | {content}"
        case RenderLayout_Vertical():
            rendered = f"Result\n{content}"

    return Ok(value=rendered)
