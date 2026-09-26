from cott_runtime import CottList

from real.harlequin.adapters_types import AdapterKind, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite
from real.harlequin.catalog_types import CatalogEntry, CatalogKind, CatalogKind_Database, CatalogKind_Schema, CatalogKind_Table, CatalogKind_TemporaryTable, CatalogKind_View


def _duckdb(kind: CatalogKind) -> list[str]:
    if isinstance(kind, CatalogKind_Database):
        return ["Switch Editor Context (Use)", "Export Database"]
    if isinstance(kind, CatalogKind_Schema):
        return ["Switch Editor Context (Use)", "Drop Schema"]
    base = ["Insert Columns at Cursor", "Preview Data", "Describe", "Summarize", "Show DDL"]
    if isinstance(kind, (CatalogKind_Table, CatalogKind_TemporaryTable)):
        return [*base, "Drop Table"]
    if isinstance(kind, CatalogKind_View):
        return [*base, "Drop View"]
    return []


def _sqlite(kind: CatalogKind) -> list[str]:
    base = ["Insert Columns at Cursor", "Preview Data", "Describe", "Show DDL"]
    if isinstance(kind, CatalogKind_Table):
        return [*base, "Drop Table"]
    if isinstance(kind, CatalogKind_View):
        return [*base, "Drop View"]
    return []


def _postgres(kind: CatalogKind) -> list[str]:
    base = ["Insert Columns at Cursor", "Preview Data", "Describe Relation (\\\\d+)"]
    if isinstance(kind, CatalogKind_Table):
        return [*base, "Describe Indexes", "Describe Constraints", "Drop Table"]
    if isinstance(kind, CatalogKind_View):
        return [*base, "Show View Definition", "Drop View"]
    if isinstance(kind, CatalogKind_Schema):
        return ["Set Search Path", "List Relations (\\\\d+)", "List Indexes (\\\\di+)", "Drop Schema"]
    if isinstance(kind, CatalogKind_Database):
        return ["List Relations (\\\\d+)", "List Indexes (\\\\di+)", "Drop Database"]
    return []


def _simple(kind: CatalogKind, use_label: str) -> list[str]:
    if isinstance(kind, CatalogKind_Table):
        return ["Insert Columns at Cursor", "Preview Data", "Drop Table"]
    if isinstance(kind, CatalogKind_View):
        return ["Insert Columns at Cursor", "Preview Data", "Drop View"]
    if isinstance(kind, CatalogKind_Database):
        return [use_label, "Drop Database"]
    return []


def catalog_interactions(adapter: AdapterKind, entry: CatalogEntry) -> CottList[str]:
    kind = entry.kind
    if isinstance(adapter, AdapterKind_DuckDb):
        items = _duckdb(kind)
    elif isinstance(adapter, AdapterKind_Sqlite):
        items = _sqlite(kind)
    elif isinstance(adapter, AdapterKind_Postgres):
        items = _postgres(kind)
    elif isinstance(adapter, AdapterKind_MySql):
        items = _simple(kind, "Set Editor Context (USE)")
    elif isinstance(adapter, AdapterKind_Odbc):
        items = _simple(kind, "Use Database")
    else:
        items = []
    return CottList(values=items)
