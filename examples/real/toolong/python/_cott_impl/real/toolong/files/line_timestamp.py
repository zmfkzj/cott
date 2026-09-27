from cott_runtime import CottList, U8, U64
from real.toolong.files import read_lines
from real.toolong.files_types import TimestampAt
from real.toolong.index import line_location
from real.toolong.model_types import LogSource, TabIndex
from real.toolong.timestamps import default_timestamp_order, scan_timestamp


def line_timestamp(sources: CottList[LogSource], index: TabIndex, line: U64, orders: CottList[CottList[U8]]) -> TimestampAt:
    location = line_location(index, line)
    file_index = location.file
    filled: list[CottList[U8]] = []
    for order in orders:
        filled.append(order)
    while len(filled) <= file_index:
        filled.append(default_timestamp_order())

    text = ""
    position = 0
    for source in sources:
        if position == file_index:
            for value in read_lines(source, CottList(values=[location.span])):
                text = value
            break
        position += 1

    scan = scan_timestamp(text, filled[file_index])
    filled[file_index] = scan.order
    return TimestampAt(timestamp=scan.timestamp, orders=CottList(values=filled))
