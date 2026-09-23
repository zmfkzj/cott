from cott_runtime import CottList
from real.harlequin.catalog_types import CatalogMatch


def render_catalog_matches(catalog_matches: CottList[CatalogMatch]) -> str:
    return "\n".join(str(match) for match in catalog_matches)
