import json

from cott_runtime import U64, CottList, Option, Some
from real.harlequin.results_types import ColumnInfo


def stats_json(status: str, statements: U64, rows: U64, truncated: bool, limit: Option[U64], elapsed_ms: U64, columns: CottList[ColumnInfo], failure_text: Option[str]) -> str:
    payload: dict[str, object] = {
        "status": status,
        "statements": statements,
        "rows": rows,
        "truncated": truncated,
        "limit": limit.value if isinstance(limit, Some) else None,
        "elapsed_ms": elapsed_ms,
        "columns": [{"name": column.name, "type": column.type_label} for column in columns],
    }
    if isinstance(failure_text, Some):
        payload["error"] = failure_text.value
    return json.dumps(payload, separators=(",", ":")) + "\n"
