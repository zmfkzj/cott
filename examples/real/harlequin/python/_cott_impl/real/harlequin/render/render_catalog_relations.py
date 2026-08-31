from cott_runtime import CottList
from real.harlequin.catalog_types import CatalogRelation


def render_catalog_relations(relations: CottList[CatalogRelation]) -> str:
    return "\n".join(str(relation) for relation in relations)
