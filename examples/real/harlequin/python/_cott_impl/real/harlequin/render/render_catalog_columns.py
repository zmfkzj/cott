from cott_runtime import CottList, Some
from real.harlequin.catalog_types import CatalogColumn


def render_catalog_columns(columns: CottList[CatalogColumn]) -> str:
    lines: list[str] = []
    for column in columns:
        line = f"{column.relation}.{column.name}"
        if column.declared_type != "":
            line += " " + column.declared_type
        if column.not_null:
            line += " NOT NULL"
        default_sql = column.default_sql
        if isinstance(default_sql, Some):
            line += " DEFAULT " + default_sql.value
        if column.primary_key_position != 0:
            line += f" PRIMARY KEY {column.primary_key_position}"
        lines.append(line)
    return "\n".join(lines)
