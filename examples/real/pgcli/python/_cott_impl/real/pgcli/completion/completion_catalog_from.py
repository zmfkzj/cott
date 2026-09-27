from typing import Literal

from cott_runtime import CottList, Opaque, Option, Some
from real.pgcli.completion_types import CompletionMetadata, FunctionMetadata, RelationMetadata


def _relations(rows: CottList[RelationMetadata]) -> list[tuple[str, str, list[tuple[str, str, bool, str | None]]]]:
    result: list[tuple[str, str, list[tuple[str, str, bool, str | None]]]] = []
    for relation in rows:
        columns: list[tuple[str, str, bool, str | None]] = []
        for column in relation.columns:
            default = column.default
            columns.append((column.name, column.datatype, column.has_default, default.value if isinstance(default, Some) else None))
        result.append((relation.schema, relation.name, columns))
    return result


def _optional_list(value: Option[CottList[str]]) -> list[str] | None:
    if isinstance(value, Some):
        return list(value.value)
    return None


def _function_row(function: FunctionMetadata) -> tuple[str, str, list[str] | None, list[str] | None, list[str] | None, str, bool, bool, bool, bool, str | None]:
    defaults = function.arg_defaults
    return (
        function.schema_name,
        function.func_name,
        _optional_list(function.arg_names),
        _optional_list(function.arg_types),
        _optional_list(function.arg_modes),
        function.return_type,
        function.is_aggregate,
        function.is_window,
        function.is_set_returning,
        function.is_extension,
        defaults.value if isinstance(defaults, Some) else None,
    )


def completion_catalog_from(metadata: CompletionMetadata) -> Opaque[Literal["pgcli.completion-catalog"]]:
    value: dict[str, object] = {
        "schemata": list(metadata.schemata),
        "tables": _relations(metadata.tables),
        "views": _relations(metadata.views),
        "functions": [_function_row(function) for function in metadata.functions],
        "datatypes": [(datatype.schema, datatype.name) for datatype in metadata.datatypes],
        "foreign_keys": [
            (key.parent_schema, key.parent_table, key.parent_column, key.child_schema, key.child_table, key.child_column)
            for key in metadata.foreign_keys
        ],
        "databases": list(metadata.databases),
        "search_path": list(metadata.search_path),
        "casing": list(metadata.casing),
    }
    return Opaque(tag="pgcli.completion-catalog", value=value)
