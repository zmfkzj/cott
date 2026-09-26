from cott_runtime import I64
from real.harlequin.hsql_types import HsqlError, HsqlError_Connection, HsqlError_Interrupted, HsqlError_Query, HsqlError_Timeout, HsqlError_Usage


def hsql_exit_status(failure: HsqlError) -> I64:
    if isinstance(failure, HsqlError_Usage):
        return 2
    if isinstance(failure, HsqlError_Query):
        return 1
    if isinstance(failure, HsqlError_Connection):
        return 3
    if isinstance(failure, HsqlError_Timeout):
        return 4
    if isinstance(failure, HsqlError_Interrupted):
        return 130
    return 70
