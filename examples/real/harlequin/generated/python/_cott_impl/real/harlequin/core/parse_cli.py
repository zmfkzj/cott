from pathlib import Path

from cott_runtime import CottList, Err, Nothing, Ok, Option, Result, Some
from real.harlequin.core_types import (
    AdapterKind,
    AdapterKind_Adbc,
    AdapterKind_BigQuery,
    AdapterKind_Cassandra,
    AdapterKind_Databricks,
    AdapterKind_DuckDb,
    AdapterKind_MySql,
    AdapterKind_NebulaGraph,
    AdapterKind_Odbc,
    AdapterKind_PostgreSql,
    AdapterKind_Sqlite,
    AdapterKind_Trino,
    CliError,
    CliError_ConflictingConnectionInputs,
    CliError_InvalidAdapter,
    CliError_MissingOptionValue,
    CliError_UnknownOption,
    CliOptions,
)


def parse_cli(arguments: CottList[str]) -> Result[CliOptions, CliError]:
    profile: Option[str] = Nothing()
    adapter: Option[AdapterKind] = Nothing()
    connection: Option[str] = Nothing()
    query_file: Option[Path] = Nothing()
    read_only = False
    no_config = False
    profile_provided = False
    connection_provided = False
    source_argument_count = 0
    index = 0

    while index < len(arguments):
        argument = arguments[index]
        if argument == "--profile":
            if index + 1 >= len(arguments):
                return Err(error=CliError_MissingOptionValue(option=argument))
            profile = Some(value=arguments[index + 1])
            profile_provided = True
            index += 2
            continue
        if argument == "--adapter":
            if index + 1 >= len(arguments):
                return Err(error=CliError_MissingOptionValue(option=argument))
            adapter_name = arguments[index + 1].lower()
            if adapter_name == "duckdb":
                adapter = Some(value=AdapterKind_DuckDb())
            elif adapter_name == "sqlite":
                adapter = Some(value=AdapterKind_Sqlite())
            elif adapter_name == "postgresql" or adapter_name == "postgres":
                adapter = Some(value=AdapterKind_PostgreSql())
            elif adapter_name == "mysql":
                adapter = Some(value=AdapterKind_MySql())
            elif adapter_name == "odbc":
                adapter = Some(value=AdapterKind_Odbc())
            elif adapter_name == "bigquery":
                adapter = Some(value=AdapterKind_BigQuery())
            elif adapter_name == "trino":
                adapter = Some(value=AdapterKind_Trino())
            elif adapter_name == "databricks":
                adapter = Some(value=AdapterKind_Databricks())
            elif adapter_name == "adbc":
                adapter = Some(value=AdapterKind_Adbc())
            elif adapter_name == "cassandra":
                adapter = Some(value=AdapterKind_Cassandra())
            elif adapter_name == "nebulagraph" or adapter_name == "nebula":
                adapter = Some(value=AdapterKind_NebulaGraph())
            else:
                return Err(error=CliError_InvalidAdapter(value=arguments[index + 1]))
            index += 2
            continue
        if argument == "--query-file":
            if index + 1 >= len(arguments):
                return Err(error=CliError_MissingOptionValue(option=argument))
            query_file = Some(value=Path(arguments[index + 1]))
            index += 2
            continue
        if argument == "--read-only":
            read_only = True
            index += 1
            continue
        if argument == "--no-config":
            no_config = True
            index += 1
            continue
        if argument.startswith("-"):
            return Err(error=CliError_UnknownOption(argument=argument))

        source_argument_count += 1
        if connection_provided:
            return Err(error=CliError_ConflictingConnectionInputs())
        connection = Some(value=argument)
        connection_provided = True
        index += 1

    if profile_provided and connection_provided:
        return Err(error=CliError_ConflictingConnectionInputs())

    return Ok(
        value=CliOptions(
            profile=profile,
            adapter=adapter,
            connection=connection,
            query_file=query_file,
            read_only=read_only,
            no_config=no_config,
            source_argument_count=source_argument_count,
        )
    )
