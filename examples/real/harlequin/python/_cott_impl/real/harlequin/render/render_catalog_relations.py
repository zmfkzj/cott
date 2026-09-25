from cott_runtime import CottList

from real.harlequin.catalog_types import CatalogRelation, RelationKind_Table


def render_catalog_relations(relations: CottList[CatalogRelation]) -> str:
    lines: list[str] = []
    for relation in relations:
        if isinstance(relation.kind, RelationKind_Table):
            lines.append("table " + relation.name)
        else:
            lines.append("view " + relation.name)
    return "\n".join(lines)
