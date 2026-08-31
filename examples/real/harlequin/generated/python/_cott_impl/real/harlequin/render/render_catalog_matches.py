from cott_runtime import CottList
from real.harlequin.catalog_types import CatalogMatch


def render_catalog_matches(catalog_matches: CottList[CatalogMatch]) -> str:
    return "\n".join(str(catalog_match) for catalog_match in catalog_matches)
