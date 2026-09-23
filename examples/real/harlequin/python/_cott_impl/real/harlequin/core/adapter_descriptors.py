from cott_runtime import CottList
from real.harlequin.core_types import AdapterDescriptor, AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_PostgreSql, AdapterKind_Sqlite, AdapterKind_Trino


def _descriptor(kind: AdapterKind, display_name: str, schemes: CottList[str], transactions: bool, catalog: bool, files: bool) -> AdapterDescriptor:
    return AdapterDescriptor(
        kind=kind,
        display_name=display_name,
        uri_schemes=schemes,
        supports_transactions=transactions,
        supports_catalog=catalog,
        supports_files=files,
    )


def adapter_descriptors() -> CottList[AdapterDescriptor]:
    return CottList(
        values=[
            _descriptor(AdapterKind_DuckDb(), "DuckDB", CottList(values=["duckdb"]), True, True, True),
            _descriptor(AdapterKind_Sqlite(), "SQLite", CottList(values=["sqlite"]), True, True, True),
            _descriptor(AdapterKind_PostgreSql(), "PostgreSQL", CottList(values=["postgres", "postgresql"]), True, True, False),
            _descriptor(AdapterKind_MySql(), "MySQL", CottList(values=["mysql"]), True, True, False),
            _descriptor(AdapterKind_Odbc(), "ODBC", CottList(values=["odbc"]), True, True, False),
            _descriptor(AdapterKind_BigQuery(), "BigQuery", CottList(values=["bigquery"]), False, True, False),
            _descriptor(AdapterKind_Trino(), "Trino", CottList(values=["trino"]), False, True, False),
            _descriptor(AdapterKind_Databricks(), "Databricks", CottList(values=["databricks"]), False, True, True),
            _descriptor(AdapterKind_Adbc(), "ADBC", CottList(values=["adbc"]), True, True, False),
            _descriptor(AdapterKind_Cassandra(), "Cassandra", CottList(values=["cassandra"]), False, True, False),
            _descriptor(AdapterKind_NebulaGraph(), "NebulaGraph", CottList(values=["nebula"]), False, True, False),
        ]
    )
