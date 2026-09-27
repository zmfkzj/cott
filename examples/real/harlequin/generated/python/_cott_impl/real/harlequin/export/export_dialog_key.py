import os
import pathlib

from cott_runtime import CottList, Option, Some, U64

from real.harlequin.export import export_formats, format_for_path
from real.harlequin.export_types import ExportDialog, ExportFocus, ExportFocus_Cancel, ExportFocus_Export, ExportFocus_Format, ExportFocus_Option, ExportFocus_Path, ExportFormatSpec, ExportOptionKind_Choice, ExportOptionKind_Flag, ExportOptionSpec, ExportOptionValue, ExportOutcome, ExportOutcome_Cancel, ExportOutcome_Export, ExportOutcome_Stay, ExportRequest, ExportStep


def _spec(name: Option[str]) -> ExportFormatSpec | None:
    if isinstance(name, Some):
        for spec in export_formats():
            if spec.name == name.value:
                return spec
    return None


def _defaults(name: Option[str]) -> CottList[ExportOptionValue]:
    spec = _spec(name)
    if spec is None:
        return CottList(values=[])
    return CottList(values=[ExportOptionValue(name=option.name, value=option.default) for option in spec.options])


def _options(dialog: ExportDialog) -> list[ExportOptionSpec]:
    spec = _spec(dialog.format)
    return [] if spec is None else list(spec.options)


def _with(path: str, cursor: U64, fmt: Option[str], values: CottList[ExportOptionValue], focus: ExportFocus, message: str) -> ExportDialog:
    return ExportDialog(path=path, path_cursor=cursor, format=fmt, values=values, focus=focus, message=message)


def _stay(dialog: ExportDialog) -> ExportStep:
    return ExportStep(dialog=dialog, outcome=ExportOutcome_Stay())


def _focus_list(dialog: ExportDialog) -> list[ExportFocus]:
    items: list[ExportFocus] = [ExportFocus_Path(), ExportFocus_Format()]
    items.extend(ExportFocus_Option(index=index) for index in range(len(_options(dialog))))
    items.append(ExportFocus_Cancel())
    items.append(ExportFocus_Export())
    return items


def _move_focus(dialog: ExportDialog, delta: int) -> ExportDialog:
    items = _focus_list(dialog)
    current = 0
    for index, item in enumerate(items):
        if item == dialog.focus:
            current = index
            break
    focus = items[(current + delta) % len(items)]
    return _with(dialog.path, dialog.path_cursor, dialog.format, dialog.values, focus, dialog.message)


def _printable(key: str, text: str) -> bool:
    return text != "" and text.isprintable() and key not in ("enter", "tab", "shift+tab", "escape", "backspace", "delete")


def _value_of(dialog: ExportDialog, name: str) -> str:
    for value in dialog.values:
        if value.name == name:
            return value.value
    return ""


def _set_value(dialog: ExportDialog, name: str, value: str) -> ExportDialog:
    values = CottList(values=[ExportOptionValue(name=item.name, value=value if item.name == name else item.value) for item in dialog.values])
    return _with(dialog.path, dialog.path_cursor, dialog.format, values, dialog.focus, "")


def _validate(dialog: ExportDialog) -> ExportStep:
    message = ""
    fmt = dialog.format
    if dialog.path == "":
        message = "A file path is required."
    elif dialog.path.endswith("/"):
        message = "Path is not a file"
    elif not isinstance(fmt, Some):
        message = "Must select format. Supported formats: CSV, Parquet, JSON, ORC, Feather"
    else:
        for option in _options(dialog):
            value = _value_of(dialog, option.name)
            if value == "" and option.allow_empty:
                continue
            if option.integer:
                try:
                    int(value)
                except ValueError:
                    message = f"{option.label} must be a whole number."
                    break
            elif option.number:
                try:
                    float(value)
                except ValueError:
                    message = f"{option.label} must be a number."
                    break
    if message != "" or not isinstance(fmt, Some):
        return _stay(_with(dialog.path, dialog.path_cursor, fmt, dialog.values, dialog.focus, message))
    request = ExportRequest(path=pathlib.Path(os.path.expanduser(dialog.path)), format=fmt.value, options=dialog.values)
    outcome: ExportOutcome = ExportOutcome_Export(request=request)
    return ExportStep(dialog=dialog, outcome=outcome)


def _path_key(dialog: ExportDialog, key: str, text: str) -> ExportStep:
    if key == "enter":
        return _validate(dialog)
    path = dialog.path
    cursor = min(dialog.path_cursor, len(path))
    if key == "left":
        cursor = max(0, cursor - 1)
    elif key == "right":
        cursor = min(len(path), cursor + 1)
    elif key == "home":
        cursor = 0
    elif key == "end":
        cursor = len(path)
    elif key == "backspace":
        if cursor == 0:
            return _stay(dialog)
        path = path[:cursor - 1] + path[cursor:]
        cursor -= 1
    elif key == "delete":
        if cursor == len(path):
            return _stay(dialog)
        path = path[:cursor] + path[cursor + 1:]
    elif _printable(key, text):
        path = path[:cursor] + text + path[cursor:]
        cursor += len(text)
    else:
        return _stay(dialog)
    if key in ("left", "right", "home", "end"):
        return _stay(_with(path, cursor, dialog.format, dialog.values, dialog.focus, dialog.message))
    fmt = dialog.format
    values = dialog.values
    inferred = format_for_path(path)
    if isinstance(inferred, Some) and not (isinstance(fmt, Some) and fmt.value == inferred.value):
        fmt = Some(value=inferred.value)
        values = _defaults(fmt)
    return _stay(_with(path, cursor, fmt, values, dialog.focus, ""))


def _format_key(dialog: ExportDialog, key: str) -> ExportStep:
    if key not in ("left", "right", "enter"):
        return _stay(dialog)
    names = [spec.name for spec in export_formats()]
    current = -1
    fmt0 = dialog.format
    if isinstance(fmt0, Some):
        for index, name in enumerate(names):
            if name == fmt0.value:
                current = index
                break
    if current < 0:
        index = len(names) - 1 if key == "left" else 0
    else:
        index = (current + (-1 if key == "left" else 1)) % len(names)
    fmt: Option[str] = Some(value=names[index])
    return _stay(_with(dialog.path, dialog.path_cursor, fmt, _defaults(fmt), dialog.focus, ""))


def _option_key(dialog: ExportDialog, index: U64, key: str, text: str) -> ExportStep:
    options = _options(dialog)
    if index >= len(options):
        return _stay(dialog)
    option = options[index]
    value = _value_of(dialog, option.name)
    kind = option.kind
    if isinstance(kind, ExportOptionKind_Flag):
        if key in ("enter", "space"):
            return _stay(_set_value(dialog, option.name, "false" if value == "true" else "true"))
        return _stay(dialog)
    if isinstance(kind, ExportOptionKind_Choice):
        if key not in ("left", "right", "enter"):
            return _stay(dialog)
        choices = list(kind.values)
        if not choices:
            return _stay(dialog)
        current = choices.index(value) if value in choices else -1
        if current < 0:
            new = len(choices) - 1 if key == "left" else 0
        else:
            new = (current + (-1 if key == "left" else 1)) % len(choices)
        return _stay(_set_value(dialog, option.name, choices[new]))
    if key == "backspace":
        if value == "":
            return _stay(dialog)
        return _stay(_set_value(dialog, option.name, value[:-1]))
    if _printable(key, text):
        return _stay(_set_value(dialog, option.name, value + text))
    return _stay(dialog)


def export_dialog_key(dialog: ExportDialog, key: str, text: str) -> ExportStep:
    if key == "escape":
        return ExportStep(dialog=dialog, outcome=ExportOutcome_Cancel())
    if key == "tab":
        return _stay(_move_focus(dialog, 1))
    if key == "shift+tab":
        return _stay(_move_focus(dialog, -1))
    focus = dialog.focus
    if isinstance(focus, ExportFocus_Path):
        return _path_key(dialog, key, text)
    if isinstance(focus, ExportFocus_Format):
        return _format_key(dialog, key)
    if isinstance(focus, ExportFocus_Option):
        return _option_key(dialog, focus.index, key, text)
    if isinstance(focus, ExportFocus_Cancel):
        if key == "enter":
            return ExportStep(dialog=dialog, outcome=ExportOutcome_Cancel())
        return _stay(dialog)
    if key == "enter":
        return _validate(dialog)
    return _stay(dialog)
