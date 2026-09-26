from real.harlequin.hsql_types import HsqlError, HsqlError_Connection, HsqlError_Interrupted, HsqlError_Query, HsqlError_Timeout, HsqlError_Usage


def hsql_error_line(failure: HsqlError) -> str:
    if isinstance(failure, HsqlError_Usage):
        return f"hsql: error: {failure.message}\n"
    if isinstance(failure, HsqlError_Query):
        return f"hsql: error: {failure.message}\n"
    if isinstance(failure, HsqlError_Connection):
        return f"hsql: error: {failure.message}\n"
    if isinstance(failure, HsqlError_Timeout):
        return f"hsql: error: {failure.message}\n"
    if isinstance(failure, HsqlError_Interrupted):
        return "hsql: error: interrupted\n"
    return f"hsql: error: hsql hit a bug in itself and could not finish the run.\nnote: {failure.message}\n"
