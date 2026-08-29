from cott_runtime import CottList, Nothing, Some
from real.harlequin.catalog_types import CatalogColumn


def _escape_text(text: str) -> str:
    return text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


def _render_grid(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            if len(value) > widths[index]:
                widths[index] = len(value)

    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
    lines = [border, "|" + "|".join(f" {header:<{widths[index]}} " for index, header in enumerate(headers)) + "|", border]
    for row in rows:
        lines.append("|" + "|".join(f" {value:<{widths[index]}} " for index, value in enumerate(row)) + "|")
    lines.append(border)
    return "\n".join(lines)


def render_catalog_columns(columns: CottList[CatalogColumn]) -> str:
    """Render catalog columns in deterministic table order."""
    rows: list[tuple[str, ...]] = []
    for column in sorted(columns, key=lambda item: item.ordinal):
        match column.default_sql:
            case Some(value=default_sql):
                rendered_default = _escape_text(default_sql)
            case Nothing():
                rendered_default = "NULL"
        rows.append(
            (
                _escape_text(column.relation),
                str(column.ordinal),
                _escape_text(column.name),
                _escape_text(column.declared_type),
                "true" if column.not_null else "false",
                rendered_default,
                str(column.primary_key_position),
            )
        )
    return _render_grid(
        ("relation", "ordinal", "name", "declared_type", "not_null", "default_sql", "primary_key_position"),
        rows,
    )
