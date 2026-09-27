from typing import Final

from cott_runtime import CottList, Some, U64
from wcwidth import wcwidth

from real.harlequin.export import export_formats
from real.harlequin.export_types import ExportDialog, ExportFocus_Cancel, ExportFocus_Export, ExportFocus_Format, ExportFocus_Option, ExportFocus_Path, ExportFormatSpec, ExportOptionKind_Choice, ExportOptionKind_Flag, ExportOptionSpec
from real.harlequin.style_types import StyledLine, StyledSpan

_PLACEHOLDER: Final[str] = "/path/to/file  (tab autocompletes, enter exports, esc cancels)"


def _cut(spans: list[StyledSpan], width: U64) -> StyledLine:
    clipped: list[StyledSpan] = []
    remaining = width
    for span in spans:
        if remaining == 0:
            break
        text = span.text.replace("\r", " ").replace("\n", " ")
        end = 0
        for character in text:
            cells = wcwidth(character)
            if cells < 0:
                cells = 1
            if cells > remaining:
                break
            remaining -= cells
            end += 1
        clipped.append(StyledSpan(style=span.style, text=text[:end]))
        if end < len(text):
            break
    return StyledLine(spans=CottList(values=clipped))


def _focus_style(base: str, focused: bool) -> str:
    if focused:
        return base + " class:hq.cursor" if base else "class:hq.cursor"
    return base


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
        for choice, label in zip(kind.values, kind.labels):
            if choice == value:
                return label
    return value


def render_export_dialog(dialog: ExportDialog, width: U64) -> CottList[StyledLine]:
    focus = dialog.focus
    lines: list[StyledLine] = [
        _cut([StyledSpan(style="class:hq.dialog.title", text="Data Exporter")], width),
        _cut([StyledSpan(style="class:hq.text", text="Export the results of your query to a file.")], width),
    ]
    if dialog.path:
        lines.append(_cut([StyledSpan(style=_focus_style("", isinstance(focus, ExportFocus_Path)), text=dialog.path)], width))
    else:
        lines.append(_cut([StyledSpan(style=_focus_style("class:hq.muted", isinstance(focus, ExportFocus_Path)), text=_PLACEHOLDER)], width))
    if dialog.message:
        lines.append(_cut([StyledSpan(style="class:hq.error", text=dialog.message)], width))

    selected = dialog.format
    spec: ExportFormatSpec | None = None
    if isinstance(selected, Some):
        for candidate in export_formats():
            if candidate.name == selected.value:
                spec = candidate
                break
    label = spec.label if spec is not None else "Select a format"
    lines.append(_cut([
        StyledSpan(style="", text="Format: "),
        StyledSpan(style=_focus_style("", isinstance(focus, ExportFocus_Format)), text=label),
    ], width))
    if spec is not None:
        for index, option in enumerate(spec.options):
            focused = isinstance(focus, ExportFocus_Option) and focus.index == index
            lines.append(_cut([
                StyledSpan(style="", text=option.label + ": "),
                StyledSpan(style=_focus_style("", focused), text=_option_value(dialog, option)),
            ], width))

    lines.append(_cut([
        StyledSpan(style="class:hq.button.focused" if isinstance(focus, ExportFocus_Cancel) else "class:hq.button", text="[ Cancel ]"),
        StyledSpan(style="", text="  "),
        StyledSpan(style="class:hq.button.focused" if isinstance(focus, ExportFocus_Export) else "class:hq.button", text="[ Export ]"),
    ], width))
    return CottList(values=lines)
