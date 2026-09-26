import psycopg
import psycopg.conninfo
from cott_runtime import Err, Ok, Result, Some
from real.pgcli.connection_types import ConnectError, ConnectError_AliasMissing, ConnectTarget, ConnectTarget_Alias, ConnectTarget_Conninfo, ConnectTarget_Params, ConnectTarget_Service, ConnectTarget_Uri, TargetRequest


def select_connect_target(request: TargetRequest) -> Result[ConnectTarget, ConnectError]:
    dbname_option = request.dbname_option
    dbname_argument = request.dbname_argument
    username_argument = request.username_argument
    username = username_argument.value if isinstance(username_argument, Some) else ""
    if isinstance(dbname_option, Some) and isinstance(dbname_argument, Some):
        username = dbname_argument.value

    if isinstance(dbname_option, Some):
        database = dbname_option.value
    elif isinstance(dbname_argument, Some):
        database = dbname_argument.value
    else:
        database = ""

    username_option = request.username_option
    user = username_option.value if isinstance(username_option, Some) else username
    pgservice = request.pgservice
    service: str | None = None
    if database.startswith("service="):
        service = database[8:]
    elif isinstance(pgservice, Some):
        service = pgservice.value

    is_conn_string = "://" in database or ("=" in database and service is None)
    if request.list_or_ping:
        if database == "":
            database = "postgres"
        elif is_conn_string:
            try:
                params = psycopg.conninfo.conninfo_to_dict(database)
            except psycopg.Error:
                params = None
            if params is not None:
                dbname = params.get("dbname")
                if dbname is None or str(dbname) == "":
                    database = psycopg.conninfo.make_conninfo(database, dbname="postgres")

    if request.dsn_alias != "":
        for entry in request.alias_dsn:
            if entry.name == request.dsn_alias:
                return Ok(value=ConnectTarget_Alias(name=request.dsn_alias, uri=entry.value))
        return Err(error=ConnectError_AliasMissing(name=request.dsn_alias))
    if "://" in database:
        return Ok(value=ConnectTarget_Uri(uri=database))
    if "=" in database and service is None:
        return Ok(value=ConnectTarget_Conninfo(dsn=database, user=user))
    if service is not None:
        return Ok(value=ConnectTarget_Service(service=service, user=user))
    return Ok(value=ConnectTarget_Params(database=database, host=request.host, user=user, port=request.port))
