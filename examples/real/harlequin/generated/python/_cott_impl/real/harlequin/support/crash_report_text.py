import textwrap
from typing import Final

from cott_runtime import CottList, Some
from real.harlequin.sqltext import redact_sql
from real.harlequin.support_types import CrashContext

_WIDTH: Final[int] = 72
_NOTICE: Final[str] = "Review and redact as necessary before sharing this file. It includes your configuration (with passwords masked) and, if a buffer was open, the SQL in it."


def crash_report_text(context: CrashContext, error_summary: str, traceback_text: str, reported_at: str, environment_lines: CottList[str]) -> str:
    sections: list[str] = [
        f"Harlequin crash report, {reported_at}\n" + textwrap.fill(_NOTICE, width=_WIDTH),
    ]
    sections.append("\n".join(["ENVIRONMENT", *[line for line in environment_lines]]))
    pairs: list[tuple[str, str]] = [
        ("program", context.program),
        ("adapter", context.adapter),
        ("profile", context.profile),
        ("keymaps", context.keymaps),
        ("theme", context.theme),
        ("connected", context.connected),
        ("buffer_count", context.buffer_count),
        ("terminal_size", context.terminal_size),
        ("recovery_path", context.recovery_path),
    ]
    sections.append("\n".join(["CONTEXT", *[f"{key}: {value}" for key, value in pairs]]))
    sections.append("\n".join(["TRACEBACK", error_summary, traceback_text]))
    active = context.active_sql
    if isinstance(active, Some):
        sql = redact_sql(active.value, CottList(values=[]))
        sections.append("\n".join(["SQL IN THE ACTIVE BUFFER", sql]))
    return "\n\n".join(sections) + "\n"
