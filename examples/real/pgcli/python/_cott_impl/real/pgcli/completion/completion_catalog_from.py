from typing import Literal

from cott_runtime import CottList, Opaque, Option, Some

from real.pgcli.completion_types import CompletionMetadata, FunctionMetadata, RelationMetadata


def _relations(rows: CottList[RelationMetadata]) -> list[tuple[str, str, list[tuple[str, str, bool, str | None]]]]:
    out: list[tuple[str, str, list[tuple[str, str, bool, str | None]]]] = []
    for r in rows:
        cols: list[tuple[str, str, bool, str | None]] = []
        for c in r.columns:
            d = c.default
            cols.append((c.name, c.datatype, c.has_default, d.value if isinstance(d, Some) else None))
        out.append((r.schema, r.name, cols))
    return out


def _opt_list(value: Option[CottList[str]]) -> list[str] | None:
    if isinstance(value, Some):
        return [x for x in value.value]
    return None


def _function_row(f: FunctionMetadata) -> tuple[str, str, list[str] | None, list[str] | None, list[str] | None, str, bool, bool, bool, bool, str | None]:
    d = f.arg_defaults
    return (
        f.schema_name,
        f.func_name,
        _opt_list(f.arg_names),
        _opt_list(f.arg_types),
        _opt_list(f.arg_modes),
        f.return_type,
        f.is_aggregate,
        f.is_window,
        f.is_set_returning,
        f.is_extension,
        d.value if isinstance(d, Some) else None,
    )


def completion_catalog_from(metadata: CompletionMetadata) -> Opaque[Literal["pgcli.completion-catalog"]]:
    value: dict[str, object] = {
        "schemata": [s for s in metadata.schemata],
        "tables": _relations(metadata.tables),
        "views": _relations(metadata.views),
        "functions": [_function_row(f) for f in metadata.functions],
        "datatypes": [(t.schema, t.name) for t in metadata.datatypes],
        "foreign_keys": [
            (k.parent_schema, k.parent_table, k.parent_column, k.child_schema, k.child_table, k.child_column)
            for k in metadata.foreign_keys
        ],
        "databases": [s for s in metadata.databases],
        "search_path": [s for s in metadata.search_path],
        "casing": [s for s in metadata.casing],
    }
    return Opaque(tag="pgcli.completion-catalog", value=value)
