from cott_runtime import CottList, Nothing, Option, Some

from real.harlequin.adapters import catalog_interactions
from real.harlequin.adapters_types import AdapterKind, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, InteractionPlan, InteractionPlan_Execute, InteractionPlan_InsertChildNames, InteractionPlan_InsertText, InteractionPlan_NewBuffer, InteractionPlan_NewBufferFromQuery
from real.harlequin.catalog_types import CatalogEntry, CatalogKind_Database, CatalogKind_View


def _split_identifier(qi: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    quoted = False
    i = 0
    while i < len(qi):
        ch = qi[i]
        if quoted:
            if ch == '"':
                if i + 1 < len(qi) and qi[i + 1] == '"':
                    current.append('"')
                    i += 1
                else:
                    quoted = False
            else:
                current.append(ch)
        elif ch == '"':
            quoted = True
        elif ch == ".":
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current))
    return parts


def _lit(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _drop_confirm(what: str, label: str, children: CottList[CatalogEntry]) -> Option[str]:
    for _child in children:
        return Some(value=f"Really drop {what} {label} and everything in it?")
    return Nothing()


def _pg_relation_columns(qi: str) -> str:
    return (
        "select a.attname as \"Column\",\n"
        "  pg_catalog.format_type(a.atttypid, a.atttypmod) as \"Type\",\n"
        "  (select c.collname from pg_catalog.pg_collation c, pg_catalog.pg_type t\n"
        "   where c.oid = a.attcollation and t.oid = a.atttypid and a.attcollation <> t.typcollation) as \"Collation\",\n"
        "  case when a.attnotnull then 'not null' else '' end as \"Nullable\",\n"
        "  pg_catalog.pg_get_expr(d.adbin, d.adrelid, true) as \"Default\",\n"
        "  case a.attstorage when 'p' then 'plain' when 'e' then 'external' when 'm' then 'main' when 'x' then 'extended' end as \"Storage\",\n"
        "  pg_catalog.col_description(a.attrelid, a.attnum) as \"Description\"\n"
        "from pg_catalog.pg_attribute a\n"
        "left join pg_catalog.pg_attrdef d on d.adrelid = a.attrelid and d.adnum = a.attnum and a.atthasdef\n"
        f"where a.attrelid = {_lit(qi)}::regclass and a.attnum > 0 and not a.attisdropped\n"
        "order by a.attnum"
    )


def _pg_relation_indexes(qi: str) -> str:
    return (
        "select c2.relname as \"Name\", i.indisprimary as \"Primary\", i.indisunique as \"Unique\",\n"
        "  pg_catalog.pg_get_indexdef(i.indexrelid, 0, true) as \"Definition\"\n"
        "from pg_catalog.pg_index i\n"
        "join pg_catalog.pg_class c2 on c2.oid = i.indexrelid\n"
        f"where i.indrelid = {_lit(qi)}::regclass\n"
        "order by i.indisprimary desc, c2.relname"
    )


def _pg_relation_constraints(qi: str) -> str:
    return (
        "select r.conname as \"Name\", pg_catalog.pg_get_constraintdef(r.oid, true) as \"Definition\"\n"
        "from pg_catalog.pg_constraint r\n"
        f"where r.conrelid = {_lit(qi)}::regclass\n"
        "order by 1"
    )


def _pg_list_relations(schema_filter: str) -> str:
    return (
        "select n.nspname as \"Schema\", c.relname as \"Name\",\n"
        "  case c.relkind when 'r' then 'table' when 'v' then 'view' when 'm' then 'materialized view' when 'i' then 'index' when 'S' then 'sequence' when 't' then 'TOAST table' when 'f' then 'foreign table' when 'p' then 'partitioned table' when 'I' then 'partitioned index' end as \"Type\",\n"
        "  pg_catalog.pg_get_userbyid(c.relowner) as \"Owner\",\n"
        "  case c.relpersistence when 'p' then 'permanent' when 't' then 'temporary' when 'u' then 'unlogged' end as \"Persistence\",\n"
        "  pg_catalog.pg_size_pretty(pg_catalog.pg_table_size(c.oid)) as \"Size\",\n"
        "  pg_catalog.obj_description(c.oid, 'pg_class') as \"Description\"\n"
        "from pg_catalog.pg_class c\n"
        "left join pg_catalog.pg_namespace n on n.oid = c.relnamespace\n"
        "where c.relkind in ('r','p','v','m','S','f','')\n"
        f"  and {schema_filter}\n"
        "order by 1, 2"
    )


def _pg_list_indexes(schema_filter: str) -> str:
    return (
        "select n.nspname as \"Schema\", c.relname as \"Name\", 'index' as \"Type\",\n"
        "  pg_catalog.pg_get_userbyid(c.relowner) as \"Owner\", c2.relname as \"Table\",\n"
        "  case c.relpersistence when 'p' then 'permanent' when 't' then 'temporary' when 'u' then 'unlogged' end as \"Persistence\",\n"
        "  am.amname as \"Access method\",\n"
        "  pg_catalog.pg_size_pretty(pg_catalog.pg_table_size(c.oid)) as \"Size\",\n"
        "  pg_catalog.obj_description(c.oid, 'pg_class') as \"Description\"\n"
        "from pg_catalog.pg_class c\n"
        "left join pg_catalog.pg_namespace n on n.oid = c.relnamespace\n"
        "left join pg_catalog.pg_am am on am.oid = c.relam\n"
        "left join pg_catalog.pg_index i on i.indexrelid = c.oid\n"
        "left join pg_catalog.pg_class c2 on i.indrelid = c2.oid\n"
        "where c.relkind in ('i','I')\n"
        f"  and {schema_filter}\n"
        "order by 1, 2"
    )


def _pg_schema_filter(entry: CatalogEntry) -> str:
    parts = _split_identifier(entry.qualified_identifier)
    return f"n.nspname = {_lit(parts[-1])}"


def plan_interaction(adapter: AdapterKind, entry: CatalogEntry, label: str, children: CottList[CatalogEntry]) -> Option[InteractionPlan]:
    if label == "Insert Name at Cursor":
        return Some(value=InteractionPlan_InsertText(text=entry.query_name))
    listed = False
    for item in catalog_interactions(adapter, entry):
        if item == label:
            listed = True
    if not listed:
        return Nothing()
    qi = entry.qualified_identifier
    name = entry.label
    is_view = isinstance(entry.kind, CatalogKind_View)
    plan: InteractionPlan | None = None
    if label == "Insert Columns at Cursor":
        plan = InteractionPlan_InsertChildNames(parent=entry.id)
    elif label == "Preview Data":
        if isinstance(adapter, AdapterKind_MySql):
            plan = InteractionPlan_NewBuffer(text=f"select * from {qi} limit 100")
        elif isinstance(adapter, AdapterKind_Odbc):
            plan = InteractionPlan_NewBuffer(text=f"select * from {qi}")
        else:
            plan = InteractionPlan_NewBuffer(text=f"select *\nfrom {qi}\nlimit 100")
    elif label == "Describe":
        if isinstance(adapter, AdapterKind_Sqlite):
            plan = InteractionPlan_NewBuffer(text=f"pragma table_info({qi})")
        else:
            plan = InteractionPlan_NewBuffer(text=f"describe {qi}")
    elif label == "Summarize":
        plan = InteractionPlan_NewBuffer(text=f"summarize {qi}")
    elif label == "Export Database":
        plan = InteractionPlan_NewBuffer(text=f"use {qi};\nexport database './target_directory';")
    elif label == "Show DDL":
        failure = f"Could not load DDL for {name}"
        if isinstance(adapter, AdapterKind_DuckDb):
            parts = _split_identifier(qi)
            db = parts[0] if len(parts) >= 3 else ""
            schema = parts[-2] if len(parts) >= 2 else ""
            if is_view:
                sql = f"select sql from duckdb_views() where database_name = '{db}' and schema_name = '{schema}' and view_name = '{name}' limit 1"
            else:
                sql = f"select sql from duckdb_tables() where database_name = '{db}' and schema_name = '{schema}' and table_name = '{name}' limit 1"
        else:
            sql = f"select sql from sqlite_schema where tbl_name = '{name}' limit 1"
        plan = InteractionPlan_NewBufferFromQuery(sql=sql, failure=failure)
    elif label in ("Switch Editor Context (Use)", "Set Editor Context (USE)", "Use Database"):
        plan = InteractionPlan_Execute(sql=f"use {qi}", confirm=Nothing(), success=f"Editor context switched to {name}", failure="Could not switch context", refresh=False)
    elif label == "Set Search Path":
        plan = InteractionPlan_Execute(sql=f"set search_path to {qi}", confirm=Nothing(), success=f"Editor context switched to {name}", failure="Could not switch context", refresh=False)
    elif label in ("Drop Table", "Drop View"):
        what = "table" if label == "Drop Table" else "view"
        plan = InteractionPlan_Execute(sql=f"drop {what} {qi}", confirm=Some(value=f"Really drop {what} {name}?"), success=f"Dropped {what} {name}", failure=f"Could not drop {what} {name}", refresh=True)
    elif label == "Drop Schema":
        plan = InteractionPlan_Execute(sql=f"drop schema {qi} cascade", confirm=_drop_confirm("schema", name, children), success=f"Dropped schema {name}", failure=f"Could not drop schema {name}", refresh=True)
    elif label == "Drop Database":
        plan = InteractionPlan_Execute(sql=f"drop database {qi}", confirm=_drop_confirm("database", name, children), success=f"Dropped database {name}", failure=f"Could not drop database {name}", refresh=True)
    elif isinstance(adapter, AdapterKind_Postgres):
        if label == "Describe Relation (\\d+)":
            plan = InteractionPlan_NewBuffer(text=_pg_relation_columns(qi))
        elif label == "Describe Indexes":
            plan = InteractionPlan_NewBuffer(text=_pg_relation_indexes(qi))
        elif label == "Describe Constraints":
            plan = InteractionPlan_NewBuffer(text=_pg_relation_constraints(qi))
        elif label == "Show View Definition":
            plan = InteractionPlan_NewBufferFromQuery(sql=f"select pg_get_viewdef('{qi}'::regclass, true)", failure=f"Could not load view definition for {name}")
        elif label in ("List Relations (\\d+)", "List Indexes (\\di+)"):
            if isinstance(entry.kind, CatalogKind_Database):
                schema_filter = "n.nspname <> 'pg_catalog' and n.nspname !~ '^pg_toast' and n.nspname <> 'information_schema'"
            else:
                schema_filter = _pg_schema_filter(entry)
            if label == "List Relations (\\d+)":
                plan = InteractionPlan_NewBuffer(text=_pg_list_relations(schema_filter))
            else:
                plan = InteractionPlan_NewBuffer(text=_pg_list_indexes(schema_filter))
    if plan is None:
        return Nothing()
    return Some(value=plan)
