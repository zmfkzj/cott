import sys
from pathlib import Path
from typing import Never

from cott_runtime import CottList, Err, Nothing, Ok, Some
from real.pgcli import resolve_connection_plan, run_interactive
from real.pgcli_types import (
    ClientError,
    ClientError_CatalogFailed,
    ClientError_EditorFailed,
    ClientError_ExportFailed,
    ClientError_FavoriteFailed,
    ClientError_HistoryFailed,
    ClientError_ImportFailed,
    ClientError_InvalidCommand,
    ClientError_InvalidSql,
    ClientError_NotificationFailed,
    ClientError_PagerFailed,
    ClientError_QueryFailed,
    ClientError_TerminalFailed,
    ClientError_TransactionFailed,
    ClientError_UnsupportedFormat,
    ConnectionError,
    ConnectionError_CredentialUnavailable,
    ConnectionError_InvalidDsn,
    ConnectionError_InvalidPort,
    ConnectionError_MissingDatabase,
    ConnectionError_ProfileMissing,
    ConnectionError_PromptDisabled,
    ConnectionError_SshInvalid,
    ConnectionError_TlsInvalid,
    ConnectionInputs,
    ConnectionRequest,
    EnvironmentInputs,
    FavoriteStore,
    HistoryPolicy,
    InteractiveRequest,
    SessionOptions,
    SshSettings,
    TableFormat,
    TableFormat_Aligned,
    TableFormat_Csv,
    TableFormat_Html,
    TableFormat_Json,
    TableFormat_JsonLines,
    TableFormat_Latex,
    TableFormat_Markdown,
    TableFormat_Tsv,
    TableFormat_Vertical,
    TlsSettings,
    TransactionMode,
    TransactionMode_AutoCommit,
    TransactionMode_Manual,
    TransactionMode_ReadOnly,
)


def _unsigned(value: str, maximum: int) -> int:
    if value == "":
        return -1
    number = 0
    for character in value:
        if character < "0" or character > "9":
            return -1
        number = number * 10 + ord(character) - ord("0")
        if number > maximum:
            return -1
    return number


def _connection_error_text(error: ConnectionError) -> str:
    if isinstance(error, ConnectionError_MissingDatabase):
        return "database is required"
    if isinstance(error, ConnectionError_InvalidPort):
        return "invalid port: " + error.value
    if isinstance(error, ConnectionError_InvalidDsn):
        return "invalid DSN: " + error.value
    if isinstance(error, ConnectionError_ProfileMissing):
        return "connection profile not found: " + error.name
    if isinstance(error, ConnectionError_TlsInvalid):
        return "invalid TLS settings: " + error.message
    if isinstance(error, ConnectionError_SshInvalid):
        return "invalid SSH settings: " + error.message
    if isinstance(error, ConnectionError_CredentialUnavailable):
        return "credential unavailable: " + error.message
    if isinstance(error, ConnectionError_PromptDisabled):
        return "password prompting is disabled"
    return "connection failed: " + error.message


def _client_error_text(error: ClientError) -> str:
    if isinstance(error, ClientError_InvalidCommand):
        return "invalid command: " + error.source
    if isinstance(error, ClientError_InvalidSql):
        return "invalid SQL: " + error.message
    if isinstance(error, ClientError_CatalogFailed):
        return "catalog refresh failed: " + error.message
    if isinstance(error, ClientError_QueryFailed):
        return "query failed: " + error.message
    if isinstance(error, ClientError_TransactionFailed):
        return "transaction failed: " + error.message
    if isinstance(error, ClientError_ImportFailed):
        return "import failed for " + str(error.path) + ": " + error.message
    if isinstance(error, ClientError_ExportFailed):
        return "export failed for " + str(error.path) + ": " + error.message
    if isinstance(error, ClientError_HistoryFailed):
        return "history failed for " + str(error.path) + ": " + error.message
    if isinstance(error, ClientError_FavoriteFailed):
        return "favorite not found: " + error.name
    if isinstance(error, ClientError_EditorFailed):
        return "editor failed: " + error.message
    if isinstance(error, ClientError_PagerFailed):
        return "pager failed: " + error.message
    if isinstance(error, ClientError_NotificationFailed):
        return "notification failed: " + error.message
    if isinstance(error, ClientError_TerminalFailed):
        return "terminal failed: " + error.message
    return "unsupported format: " + error.value


def run(arguments: CottList[str]) -> Never:
    values: list[str] = []
    for argument in arguments:
        values.append(argument)

    dsn = ""
    profile = ""
    host = ""
    port = ""
    user = ""
    password = ""
    database = ""
    tls_mode = ""
    tls_root_certificate = Path("")
    tls_certificate = Path("")
    tls_private_key = Path("")
    ssh_host = ""
    ssh_port = 22
    ssh_user = ""
    ssh_private_key = Path("")
    ssh_supplied = False
    initial_sql = ""
    execute_once = False
    catalog_limit = 1000
    completion_limit = 100
    history_path = Path(".pgcli_history")
    history_max_entries = 1000
    history_unique = True
    favorites_path = Path(".pgcli_favorites")
    favorites_max_entries = 100
    output_format: TableFormat = TableFormat_Aligned()
    timing = False
    pager = True
    multiline = True
    transaction: TransactionMode = TransactionMode_AutoCommit()

    index = 0
    while index < len(values):
        source = values[index]
        option = source
        option_value = ""
        has_inline_value = False
        equals = source.find("=")
        if source.startswith("--") and equals >= 0:
            option = source[:equals]
            option_value = source[equals + 1 :]
            has_inline_value = True

        needs_value = option in (
            "--dsn",
            "--profile",
            "-h",
            "--host",
            "-p",
            "--port",
            "-U",
            "--user",
            "--username",
            "-W",
            "--password",
            "-d",
            "--database",
            "--dbname",
            "-c",
            "--command",
            "--execute",
            "--format",
            "--catalog-limit",
            "--completion-limit",
            "--history-file",
            "--history-max-entries",
            "--favorites-file",
            "--favorites-max-entries",
            "--transaction",
            "--sslmode",
            "--tls-mode",
            "--sslrootcert",
            "--tls-root-certificate",
            "--sslcert",
            "--tls-certificate",
            "--sslkey",
            "--tls-private-key",
            "--ssh-host",
            "--ssh-port",
            "--ssh-user",
            "--ssh-private-key",
        )
        if needs_value and not has_inline_value:
            index += 1
            if index >= len(values):
                print(_client_error_text(ClientError_InvalidCommand(source="missing value for " + option)))
                sys.exit(2)
            option_value = values[index]

        if option == "--dsn":
            dsn = option_value
        elif option == "--profile":
            profile = option_value
        elif option == "-h" or option == "--host":
            host = option_value
        elif option == "-p" or option == "--port":
            port = option_value
        elif option == "-U" or option == "--user" or option == "--username":
            user = option_value
        elif option == "-W" or option == "--password":
            password = option_value
        elif option == "-d" or option == "--database" or option == "--dbname":
            database = option_value
        elif option == "-c" or option == "--command" or option == "--execute":
            initial_sql = option_value
            execute_once = True
        elif option == "--execute-once":
            execute_once = True
        elif option == "--timing":
            timing = True
        elif option == "--no-timing":
            timing = False
        elif option == "--pager":
            pager = True
        elif option == "--no-pager":
            pager = False
        elif option == "--multiline":
            multiline = True
        elif option == "--singleline" or option == "--no-multiline":
            multiline = False
        elif option == "--history-unique":
            history_unique = True
        elif option == "--no-history-unique":
            history_unique = False
        elif option == "--format":
            folded = option_value.casefold()
            if folded == "aligned" or folded == "psql":
                output_format = TableFormat_Aligned()
            elif folded == "csv":
                output_format = TableFormat_Csv()
            elif folded == "tsv":
                output_format = TableFormat_Tsv()
            elif folded == "json":
                output_format = TableFormat_Json()
            elif folded == "jsonlines" or folded == "jsonl" or folded == "ndjson":
                output_format = TableFormat_JsonLines()
            elif folded == "html":
                output_format = TableFormat_Html()
            elif folded == "latex":
                output_format = TableFormat_Latex()
            elif folded == "markdown" or folded == "md":
                output_format = TableFormat_Markdown()
            elif folded == "vertical":
                output_format = TableFormat_Vertical()
            else:
                print(_client_error_text(ClientError_UnsupportedFormat(value=option_value)))
                sys.exit(2)
        elif option == "--transaction":
            folded = option_value.casefold()
            if folded == "auto" or folded == "autocommit" or folded == "auto-commit":
                transaction = TransactionMode_AutoCommit()
            elif folded == "manual":
                transaction = TransactionMode_Manual()
            elif folded == "readonly" or folded == "read-only":
                transaction = TransactionMode_ReadOnly()
            else:
                print(_client_error_text(ClientError_InvalidCommand(source="invalid transaction mode: " + option_value)))
                sys.exit(2)
        elif option == "--catalog-limit":
            parsed = _unsigned(option_value, 18446744073709551615)
            if parsed < 0:
                print(_client_error_text(ClientError_InvalidCommand(source="invalid catalog limit: " + option_value)))
                sys.exit(2)
            catalog_limit = parsed
        elif option == "--completion-limit":
            parsed = _unsigned(option_value, 18446744073709551615)
            if parsed < 0:
                print(_client_error_text(ClientError_InvalidCommand(source="invalid completion limit: " + option_value)))
                sys.exit(2)
            completion_limit = parsed
        elif option == "--history-file":
            history_path = Path(option_value)
        elif option == "--history-max-entries":
            parsed = _unsigned(option_value, 18446744073709551615)
            if parsed < 0:
                print(_client_error_text(ClientError_InvalidCommand(source="invalid history limit: " + option_value)))
                sys.exit(2)
            history_max_entries = parsed
        elif option == "--favorites-file":
            favorites_path = Path(option_value)
        elif option == "--favorites-max-entries":
            parsed = _unsigned(option_value, 18446744073709551615)
            if parsed < 0:
                print(_client_error_text(ClientError_InvalidCommand(source="invalid favorites limit: " + option_value)))
                sys.exit(2)
            favorites_max_entries = parsed
        elif option == "--sslmode" or option == "--tls-mode":
            tls_mode = option_value
        elif option == "--sslrootcert" or option == "--tls-root-certificate":
            tls_root_certificate = Path(option_value)
        elif option == "--sslcert" or option == "--tls-certificate":
            tls_certificate = Path(option_value)
        elif option == "--sslkey" or option == "--tls-private-key":
            tls_private_key = Path(option_value)
        elif option == "--ssh-host":
            ssh_host = option_value
            ssh_supplied = True
        elif option == "--ssh-port":
            parsed = _unsigned(option_value, 65535)
            if parsed < 0:
                print(_client_error_text(ClientError_InvalidCommand(source="invalid SSH port: " + option_value)))
                sys.exit(2)
            ssh_port = parsed
            ssh_supplied = True
        elif option == "--ssh-user":
            ssh_user = option_value
            ssh_supplied = True
        elif option == "--ssh-private-key":
            ssh_private_key = Path(option_value)
            ssh_supplied = True
        elif source.startswith("-"):
            print(_client_error_text(ClientError_InvalidCommand(source=source)))
            sys.exit(2)
        elif database == "":
            if "://" in source:
                dsn = source
            else:
                database = source
        elif initial_sql == "":
            initial_sql = source
        else:
            initial_sql = initial_sql + " " + source
        index += 1

    inputs = ConnectionInputs(host=host, port=port, user=user, password=password, database=database)
    environment = EnvironmentInputs(host="", port="", user="", password="", database="")
    tls = TlsSettings(
        mode=tls_mode,
        root_certificate=tls_root_certificate,
        certificate=tls_certificate,
        private_key=tls_private_key,
    )
    if ssh_supplied:
        ssh = Some(value=SshSettings(host=ssh_host, port=ssh_port, user=ssh_user, private_key=ssh_private_key))
    else:
        ssh = Nothing()
    connection_request = ConnectionRequest(
        dsn=dsn,
        profile=profile,
        inputs=inputs,
        environment=environment,
        tls=tls,
        ssh=ssh,
    )
    match resolve_connection_plan(connection_request, Nothing()):
        case Err(error=connection_error):
            print(_connection_error_text(connection_error))
            sys.exit(2)
        case Ok(value=connection):
            options = SessionOptions(
                connection=connection,
                catalog_limit=catalog_limit,
                completion_limit=completion_limit,
                history=HistoryPolicy(path=history_path, max_entries=history_max_entries, unique=history_unique),
                favorites=FavoriteStore(path=favorites_path, max_entries=favorites_max_entries),
                format=output_format,
                timing=timing,
                pager=pager,
                multiline=multiline,
                transaction=transaction,
            )

    request = InteractiveRequest(options=options, initial_sql=initial_sql, execute_once=execute_once)
    match run_interactive(request):
        case Ok():
            sys.exit(0)
        case Err(error=client_error):
            print(_client_error_text(client_error))
            sys.exit(1)
