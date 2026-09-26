from pathlib import Path

from cott_runtime import Err, I64, Ok, Result
from real.harlequin.support_types import CacheError, CacheError_Unwritable


def write_crash_report(directory: Path, text: str, stamp: str, pid: I64) -> Result[Path, CacheError]:
    report = directory / f"crash-{stamp}-{pid}.log"
    operation_path = directory
    try:
        directory.mkdir(parents=True, exist_ok=True)
        operation_path = report
        _ = report.write_text(text, encoding="utf-8")
        operation_path = directory
        reports = sorted(
            (path for path in directory.glob("crash-*.log") if path.is_file()),
            key=lambda path: (path.stat().st_mtime_ns, path.name),
        )
        for obsolete in reports[:-10]:
            operation_path = obsolete
            obsolete.unlink()
    except (OSError, UnicodeError, ValueError) as exc:
        return Err(error=CacheError_Unwritable(path=operation_path, message=str(exc)))
    return Ok(value=report)
