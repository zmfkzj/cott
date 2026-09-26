from cott_runtime import CottList

from real.harlequin.adapters_types import AdapterDescriptor, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Chdb, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_Postgres, AdapterKind_Sqlite, AdapterKind_Trino


def adapter_descriptors() -> CottList[AdapterDescriptor]:
    return CottList(
        values=[
            AdapterDescriptor(kind=AdapterKind_DuckDb(), name="duckdb", display_name="DuckDB", distribution="harlequin", details="This is a DuckDB adapter part of Harlequin core.", implements_read_only=True, implements_cancel=True, implements_catalog_search=True, implements_validate_sql=True),
            AdapterDescriptor(kind=AdapterKind_Sqlite(), name="sqlite", display_name="SQLite", distribution="harlequin", details="This is an SQLite adapter part of Harlequin core.", implements_read_only=True, implements_cancel=True, implements_catalog_search=True, implements_validate_sql=False),
            AdapterDescriptor(kind=AdapterKind_Postgres(), name="postgres", display_name="PostgreSQL", distribution="harlequin-postgres", details="A Harlequin adapter for Postgres.", implements_read_only=True, implements_cancel=True, implements_catalog_search=True, implements_validate_sql=False),
            AdapterDescriptor(kind=AdapterKind_MySql(), name="mysql", display_name="MySQL", distribution="harlequin-mysql", details="A Harlequin adapter for MySQL and MariaDB.", implements_read_only=True, implements_cancel=True, implements_catalog_search=True, implements_validate_sql=False),
            AdapterDescriptor(kind=AdapterKind_Odbc(), name="odbc", display_name="ODBC", distribution="harlequin-odbc", details="A Harlequin adapter for ODBC data sources.", implements_read_only=False, implements_cancel=False, implements_catalog_search=False, implements_validate_sql=False),
            AdapterDescriptor(kind=AdapterKind_BigQuery(), name="bigquery", display_name="BigQuery", distribution="harlequin-bigquery", details="A Harlequin adapter for Google BigQuery.", implements_read_only=False, implements_cancel=False, implements_catalog_search=False, implements_validate_sql=False),
            AdapterDescriptor(kind=AdapterKind_Trino(), name="trino", display_name="Trino", distribution="harlequin-trino", details="A Harlequin adapter for Trino.", implements_read_only=False, implements_cancel=False, implements_catalog_search=False, implements_validate_sql=False),
            AdapterDescriptor(kind=AdapterKind_Databricks(), name="databricks", display_name="Databricks", distribution="harlequin-databricks", details="A Harlequin adapter for Databricks.", implements_read_only=False, implements_cancel=True, implements_catalog_search=False, implements_validate_sql=False),
            AdapterDescriptor(kind=AdapterKind_Adbc(), name="adbc", display_name="ADBC", distribution="harlequin-adbc", details="A Harlequin adapter for ADBC drivers.", implements_read_only=False, implements_cancel=False, implements_catalog_search=False, implements_validate_sql=False),
            AdapterDescriptor(kind=AdapterKind_Cassandra(), name="cassandra", display_name="Cassandra", distribution="harlequin-cassandra", details="A Harlequin adapter for Apache Cassandra.", implements_read_only=False, implements_cancel=False, implements_catalog_search=False, implements_validate_sql=False),
            AdapterDescriptor(kind=AdapterKind_NebulaGraph(), name="nebulagraph", display_name="NebulaGraph", distribution="harlequin-nebulagraph", details="A Harlequin adapter for NebulaGraph.", implements_read_only=False, implements_cancel=False, implements_catalog_search=False, implements_validate_sql=False),
            AdapterDescriptor(kind=AdapterKind_Chdb(), name="chdb", display_name="chDB", distribution="harlequin-chdb", details="A Harlequin adapter for chDB, in-process ClickHouse.", implements_read_only=True, implements_cancel=True, implements_catalog_search=True, implements_validate_sql=False),
        ]
    )
