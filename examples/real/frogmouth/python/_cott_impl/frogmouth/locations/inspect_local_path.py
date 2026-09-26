import os
import stat

from cott_runtime import CottContractViolation, _cott_fixture_read
from frogmouth.model_types import PathKind, PathKind_Directory, PathKind_File, PathKind_Missing, PathKind_Other


def _inspect_host_path(path: str) -> PathKind:
    try:
        mode = os.stat(path).st_mode
    except (OSError, ValueError):
        return PathKind_Missing()
    if stat.S_ISREG(mode):
        return PathKind_File()
    if stat.S_ISDIR(mode):
        return PathKind_Directory()
    return PathKind_Other()


def inspect_local_path(path: str) -> PathKind:
    try:
        _cott_fixture_read(path)
    except CottContractViolation as error:
        if error.message == "fixture adapters are inactive":
            return _inspect_host_path(path)
        if isinstance(error.__cause__, IsADirectoryError):
            return PathKind_Directory()
        return PathKind_Missing()
    except OSError:
        return PathKind_Missing()
    return PathKind_File()
