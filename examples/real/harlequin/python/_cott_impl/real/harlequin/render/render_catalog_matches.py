from cott_runtime import CottList
from real.harlequin.catalog_types import CatalogMatch, CatalogMatchKind, CatalogMatchKind_Column, CatalogMatchKind_Relation


def _escape_text(text: str) -> str:
    return text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")


def _kind_details(kind: CatalogMatchKind) -> tuple[int, str]:
    match kind:
        case CatalogMatchKind_Relation():
            return (0, "relation")
        case CatalogMatchKind_Column():
            return (1, "column")


def _match_sort_key(catalog_match: CatalogMatch) -> tuple[str, int, int]:
    kind_order, _ = _kind_details(catalog_match.kind)
    return (catalog_match.relation, kind_order, catalog_match.ordinal)


def _ordered_matches(catalog_matches: CottList[CatalogMatch]) -> list[CatalogMatch]:
    indexed_matches: list[tuple[tuple[str, int, int], int, CatalogMatch]] = []
    for position, catalog_match in enumerate(catalog_matches):
        indexed_matches.append((_match_sort_key(catalog_match), position, catalog_match))
    indexed_matches.sort()
    return [indexed_match[2] for indexed_match in indexed_matches]


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


def render_catalog_matches(catalog_matches: CottList[CatalogMatch]) -> str:
    """Render catalog matches in deterministic table order."""
    rows: list[tuple[str, ...]] = []
    for catalog_match in _ordered_matches(catalog_matches):
        _, rendered_kind = _kind_details(catalog_match.kind)
        rows.append(
            (
                rendered_kind,
                _escape_text(catalog_match.relation),
                _escape_text(catalog_match.name),
                str(catalog_match.ordinal),
            )
        )
    return _render_grid(("kind", "relation", "name", "ordinal"), rows)
