from cott_runtime import CottList
from real.harlequin.catalog_types import CatalogMatch, CatalogMatchKind_Relation


def render_catalog_matches(catalog_matches: CottList[CatalogMatch]) -> str:
    lines: list[str] = []
    for match in catalog_matches:
        if isinstance(match.kind, CatalogMatchKind_Relation):
            lines.append("relation " + match.name)
        else:
            lines.append("column " + match.relation + "." + match.name)
    return "\n".join(lines)
