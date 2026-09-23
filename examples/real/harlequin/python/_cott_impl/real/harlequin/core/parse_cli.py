import pathlib

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.harlequin.core_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_PostgreSql, AdapterKind_Sqlite, AdapterKind_Trino, CliError, CliError_ConflictingConnectionInputs, CliError_InvalidAdapter, CliError_MissingOptionValue, CliError_UnknownOption, CliOptions


def _adapter(value: str) -> AdapterKind | None:
    name = value.strip().lower().replace("-", "").replace("_", "")
    if name == "duckdb":
        return AdapterKind_DuckDb()
    if name in ("sqlite", "sqlite3"):
        return AdapterKind_Sqlite()
    if name in ("postgres", "postgresql", "psql"):
        return AdapterKind_PostgreSql()
    if name == "mysql":
        return AdapterKind_MySql()
    if name == "odbc":
        return AdapterKind_Odbc()
    if name == "bigquery":
        return AdapterKind_BigQuery()
    if name == "trino":
        return AdapterKind_Trino()
    if name == "databricks":
        return AdapterKind_Databricks()
    if name == "adbc":
        return AdapterKind_Adbc()
    if name == "cassandra":
        return AdapterKind_Cassandra()
    if name in ("nebulagraph", "nebula"):
        return AdapterKind_NebulaGraph()
    return None


def _canonical(option: str) -> str | None:
    if option in ("--profile", "-P"):
        return "--profile"
    if option in ("--adapter", "-a"):
        return "--adapter"
    if option in ("--connection", "-c"):
        return "--connection"
    if option in ("--query-file", "-f"):
        return "--query-file"
    if option in ("--read-only", "-r"):
        return "--read-only"
    if option == "--no-config":
        return "--no-config"
    return None


def parse_cli(arguments: CottList[str]) -> Result[CliOptions, CliError]:
    args: list[str] = [a for a in arguments]
    profile: str | None = None
    adapter: AdapterKind | None = None
    connection: str | None = None
    query_file: pathlib.Path | None = None
    read_only = False
    no_config = False
    sources = 0
    only_positional = False
    i = 0
    n = len(args)
    while i < n:
        arg = args[i]
        i += 1
        if only_positional or arg == "-" or not arg.startswith("-"):
            sources += 1
            continue
        if arg == "--":
            only_positional = True
            continue
        inline: str | None = None
        name = arg
        if arg.startswith("--") and "=" in arg:
            name, _, inline = arg.partition("=")
        option = _canonical(name)
        if option is None:
            return Err(error=CliError_UnknownOption(argument=arg))
        if option in ("--read-only", "--no-config"):
            if inline is not None:
                return Err(error=CliError_UnknownOption(argument=arg))
            if option == "--read-only":
                read_only = True
            else:
                no_config = True
            continue
        if inline is None:
            if i >= n:
                return Err(error=CliError_MissingOptionValue(option=option))
            inline = args[i]
            i += 1
        if option == "--profile":
            profile = inline
        elif option == "--adapter":
            kind = _adapter(inline)
            if kind is None:
                return Err(error=CliError_InvalidAdapter(value=inline))
            adapter = kind
        elif option == "--connection":
            connection = inline
        else:
            query_file = pathlib.Path(inline)
    if connection is not None and sources > 0:
        return Err(error=CliError_ConflictingConnectionInputs())
    if no_config and profile is not None:
        return Err(error=CliError_ConflictingConnectionInputs())
    return Ok(value=CliOptions(
        profile=Some(value=profile) if profile is not None else Nothing(),
        adapter=Some(value=adapter) if adapter is not None else Nothing(),
        connection=Some(value=connection) if connection is not None else Nothing(),
        query_file=Some(value=query_file) if query_file is not None else Nothing(),
        read_only=read_only,
        no_config=no_config,
        source_argument_count=sources,
    ))
