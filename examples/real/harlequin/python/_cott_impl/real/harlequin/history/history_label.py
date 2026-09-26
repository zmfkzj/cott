from datetime import datetime, timedelta

from cott_runtime import I64, Some
from real.harlequin.history_types import QueryRecord, QueryStatus_Error, QueryStatus_Ok


def _time_text(run_at: str, timezone_offset_minutes: I64) -> str:
    try:
        moment = datetime.fromisoformat(run_at) + timedelta(minutes=timezone_offset_minutes)
        return moment.strftime("%a, %b %d %H:%M:%S")
    except (ValueError, OverflowError):
        return run_at


def history_label(record: QueryRecord, timezone_offset_minutes: I64) -> str:
    status = record.status
    if isinstance(status, QueryStatus_Ok):
        rows = record.rows
        if isinstance(rows, Some) and rows.value != 0:
            count = rows.value
            outcome = f"{count} record" if count == 1 else f"{count} records"
        else:
            outcome = "SUCCESS"
        elapsed = record.elapsed_ms
        if isinstance(elapsed, Some):
            outcome += f" in {elapsed.value / 1000:.2f}s"
    elif isinstance(status, QueryStatus_Error):
        outcome = "ERROR"
    else:
        outcome = "CANCELED"
    return f"{_time_text(record.run_at, timezone_offset_minutes)}  {outcome}"
