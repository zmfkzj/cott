from cott_runtime import CottList
from real.harlequin.catalog_types import CatalogColumn


def render_catalog_columns(columns: CottList[CatalogColumn]) -> str:
    return "\n".join(str(column) for column in columns)
