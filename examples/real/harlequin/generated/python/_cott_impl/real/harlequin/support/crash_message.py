from pathlib import Path

from cott_runtime import Option, Some


def crash_message(error_summary: str, buffers_saved: bool, report_path: Option[Path]) -> str:
    message = f"Harlequin encountered an unexpected error and had to quit.\n\n{error_summary}\n\n"
    if buffers_saved:
        message += "Your buffers have been saved, and Harlequin will offer them back the next time you start it.\n\n"
    message += "Please report this bug at https://github.com/tconbeer/harlequin/issues/new?template=crash_report.md"
    if isinstance(report_path, Some):
        message += f" and attach the crash report written to {report_path.value}"
    return message + "."
