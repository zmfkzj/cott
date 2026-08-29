from cott_runtime import CottList, Nothing, Some
from real.harlequin.catalog_types import CatalogRelation, RelationKind_Table, RelationKind_View


def _escape_text(text: str) -> str:
    return text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


def _render_grid(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            if len(value) > widths[index]:
                widths[index] = len(value)

    border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
    lines = [
        border,
        "|" + "|".join(f" {header:<{widths[index]}} " for index, header in enumerate(headers)) + "|",
        border,
    ]
    for row in rows:
        lines.append("|" + "|".join(f" {value:<{widths[index]}} " for index, value in enumerate(row)) + "|")
    lines.append(border)
    return "\n".join(lines)


def render_catalog_relations(relations: CottList[CatalogRelation]) -> str:
    """Render catalog relations in deterministic table order."""
    rows: list[tuple[str, ...]] = []
    for relation in sorted(relations, key=lambda item: item.name):
        match relation.kind:
            case RelationKind_Table():
                rendered_kind = "table"
            case RelationKind_View():
                rendered_kind = "view"
        match relation.sql:
            case Some(value=sql):
                rendered_sql = _escape_text(sql)
            case Nothing():
                rendered_sql = "NULL"
        rows.append((_escape_text(relation.name), rendered_kind, rendered_sql))
    return _render_grid(("name", "kind", "sql"), rows)
