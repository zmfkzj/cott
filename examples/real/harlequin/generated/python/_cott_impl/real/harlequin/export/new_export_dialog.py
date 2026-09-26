from cott_runtime import CottList, Nothing, Option, Some

from real.harlequin.export import export_formats, format_for_path
from real.harlequin.export_types import ExportDialog, ExportFocus_Path, ExportOptionValue


def _dialog_path(default_path: Option[str]) -> str:
    if isinstance(default_path, Some):
        path = default_path.value
        if path == "":
            return path
        last = path.rsplit("/", 1)[-1]
        if not path.endswith("/") and "." not in last:
            return path + "/"
        return path
    return ""


def new_export_dialog(default_path: Option[str]) -> ExportDialog:
    path = _dialog_path(default_path)
    fmt = format_for_path(path) if path != "" else Nothing()
    values: list[ExportOptionValue] = []
    if isinstance(fmt, Some):
        for spec in export_formats():
            if spec.name == fmt.value:
                for option in spec.options:
                    values.append(ExportOptionValue(name=option.name, value=option.default))
                break
    return ExportDialog(
        path=path,
        path_cursor=len(path),
        format=fmt,
        values=CottList(values=values),
        focus=ExportFocus_Path(),
        message="",
    )
