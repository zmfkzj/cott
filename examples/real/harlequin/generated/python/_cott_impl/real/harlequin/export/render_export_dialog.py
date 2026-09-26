from typing import Final

from cott_runtime import CottList, Some, U64

from real.harlequin.export import export_formats
from real.harlequin.export_types import ExportDialog, ExportFocus_Cancel, ExportFocus_Export, ExportFocus_Format, ExportFocus_Option, ExportFocus_Path, ExportFormatSpec, ExportOptionKind_Choice, ExportOptionKind_Flag, ExportOptionSpec
from real.harlequin.style_types import StyledLine, StyledSpan

_PLACEHOLDER: Final[str] = "/path/to/file  (tab autocompletes, enter exports, esc cancels)"


def _cut(spans: list[StyledSpan], width: int) -> StyledLine:
    out: list[StyledSpan] = []
    remaining = width
    for span in spans:
        if remaining <= 0:
            break
        text = span.text.replace("\n", " ")[:remaining]
        remaining -= len(text)
        out.append(StyledSpan(style=span.style, text=text))
    return StyledLine(spans=CottList(values=out))


def _focus_style(base: str, focused: bool) -> str:
    if not focused:
        return base
    return "class:hq.cursor" if base == "" else base + " class:hq.cursor"


def _option_value(dialog: ExportDialog, option: ExportOptionSpec) -> str:
    value = option.default
    for item in dialog.values:
        if item.name == option.name:
            value = item.value
            break
    kind = option.kind
    if isinstance(kind, ExportOptionKind_Flag):
        return "[x]" if value == "true" else "[ ]"
    if isinstance(kind, ExportOptionKind_Choice):
        values = list(kind.values)
        labels = list(kind.labels)
        if value in values:
            index = values.index(value)
            if index < len(labels):
                return labels[index]
        return value
    return value


def render_export_dialog(dialog: ExportDialog, width: U64) -> CottList[StyledLine]:
    w = int(width)
    focus = dialog.focus
    lines: list[StyledLine] = []
    lines.append(_cut([StyledSpan(style="class:hq.dialog.title", text="Data Exporter")], w))
    lines.append(_cut([StyledSpan(style="class:hq.text", text="Export the results of your query to a file.")], w))
    path_focused = isinstance(focus, ExportFocus_Path)
    if dialog.path == "":
        lines.append(_cut([StyledSpan(style=_focus_style("class:hq.muted", path_focused), text=_PLACEHOLDER)], w))
    else:
        lines.append(_cut([StyledSpan(style=_focus_style("", path_focused), text=dialog.path)], w))
    if dialog.message != "":
        lines.append(_cut([StyledSpan(style="class:hq.error", text=dialog.message)], w))
    spec: ExportFormatSpec | None = None
    selected = dialog.format
    if isinstance(selected, Some):
        for candidate in export_formats():
            if candidate.name == selected.value:
                spec = candidate
                break
    format_label = spec.label if spec is not None else "Select a format"
    lines.append(_cut([StyledSpan(style="", text="Format: "), StyledSpan(style=_focus_style("", isinstance(focus, ExportFocus_Format)), text=format_label)], w))
    if spec is not None:
        for index, option in enumerate(spec.options):
            focused = isinstance(focus, ExportFocus_Option) and int(focus.index) == index
            lines.append(_cut([StyledSpan(style="", text=option.label + ": "), StyledSpan(style=_focus_style("", focused), text=_option_value(dialog, option))], w))
    cancel_style = "class:hq.button.focused" if isinstance(focus, ExportFocus_Cancel) else "class:hq.button"
    export_style = "class:hq.button.focused" if isinstance(focus, ExportFocus_Export) else "class:hq.button"
    lines.append(_cut([StyledSpan(style=cancel_style, text="[ Cancel ]"), StyledSpan(style="", text="  "), StyledSpan(style=export_style, text="[ Export ]")], w))
    return CottList(values=lines)
