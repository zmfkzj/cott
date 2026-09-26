from cott_runtime import F64
from real.pgcli.output import duration_in_words


def timing_report(total_seconds: F64, execution_seconds: F64) -> str:
    if total_seconds > 1:
        return "Time: %0.03fs (%s), executed in: %0.03fs (%s)" % (
            total_seconds,
            duration_in_words(total_seconds),
            execution_seconds,
            duration_in_words(execution_seconds),
        )
    return "Time: %0.03fs" % total_seconds
