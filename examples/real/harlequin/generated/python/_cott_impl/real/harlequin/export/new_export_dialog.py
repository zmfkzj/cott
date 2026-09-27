from pathlib import PurePath

from cott_runtime import CottList, Nothing, Option, Some
from real.harlequin.export import export_formats, format_for_path
from real.harlequin.export_types import ExportDialog, ExportFocus_Path, ExportOptionValue


def new_export_dialog(default_path: Option[str]) -> ExportDialog:
    path = default_path.value if isinstance(default_path, Some) else ""
    if path and not path.endswith("/") and not PurePath(path).suffix:
        path += "/"

    selected: Option[str] = format_for_path(path) if path else Nothing()
    values: list[ExportOptionValue] = []
    if isinstance(selected, Some):
        for spec in export_formats():
            if spec.name == selected.value:
                values = [
                    ExportOptionValue(name=option.name, value=option.default)
                    for option in spec.options
                ]
                break

    return ExportDialog(
        path=path,
        path_cursor=len(path),
        format=selected,
        values=CottList(values=values),
        focus=ExportFocus_Path(),
        message="",
    )
