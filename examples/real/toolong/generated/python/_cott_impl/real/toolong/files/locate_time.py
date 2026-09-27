from cott_runtime import CottList, I32, Nothing, Some, U8, U64
from real.toolong.files import line_timestamp
from real.toolong.files_types import TimeJump
from real.toolong.model_types import LogSource, TabIndex, TimeUnit
from real.toolong.timestamps import compare_timestamps, shift_timestamp


def locate_time(sources: CottList[LogSource], index: TabIndex, line_count: U64, from_line: U64, steps: I32, unit: TimeUnit, orders: CottList[CottList[U8]]) -> TimeJump:
    line = from_line
    count = 0
    while True:
        current = line_timestamp(sources, index, line, orders)
        orders = current.orders
        if isinstance(current.timestamp, Some):
            start = current.timestamp.value
            break
        else:
            line += 1
            count += 1
            if count >= line_count or count > 10:
                return TimeJump(line=Nothing(), orders=orders)

    direction = 1 if steps > 0 else -1
    if direction > 0:
        line += 1
    elif line > 0:
        line -= 1
    shifted = shift_timestamp(start, steps, unit)
    if isinstance(shifted, Some):
        target = shifted.value
    else:
        return TimeJump(line=Nothing(), orders=orders)

    if direction > 0:
        while line < line_count:
            current = line_timestamp(sources, index, line, orders)
            orders = current.orders
            value = current.timestamp
            if isinstance(value, Some):
                ordering = compare_timestamps(value.value, target)
                if isinstance(ordering, Some) and ordering.value >= 0:
                    break
            line += 1
    else:
        while line > 0:
            current = line_timestamp(sources, index, line, orders)
            orders = current.orders
            value = current.timestamp
            if isinstance(value, Some):
                ordering = compare_timestamps(value.value, target)
                if isinstance(ordering, Some) and ordering.value <= 0:
                    break
            line -= 1

    if line > line_count:
        return TimeJump(line=Nothing(), orders=orders)
    return TimeJump(line=Some(value=line), orders=orders)
