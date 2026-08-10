from cott_runtime import CottList
from curriculum.json_to_csv import escape_csv_field
from curriculum.json_to_csv_types import CsvRecord


def serialize_csv(rows: CottList[CsvRecord]) -> str:
    lines = ["name,age,birthyear\r\n"]
    lines.extend(
        f"{escape_csv_field(row.name)},{escape_csv_field(row.age)},{escape_csv_field(row.birthyear)}\r\n"
        for row in rows
    )
    return "".join(lines)
