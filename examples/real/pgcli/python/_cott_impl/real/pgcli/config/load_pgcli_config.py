import os
from pathlib import Path

from cott_runtime import CottContractViolation, Err, Result, _cott_fixture_read, _cott_fixture_write
from real.pgcli.config import parse_pgcli_config
from real.pgcli.config_types import ConfigError, ConfigError_Unreadable, PGCLI_DEFAULT_CONFIG, PgcliConfig


def load_pgcli_config(path: Path) -> Result[PgcliConfig, ConfigError]:
    expanded = os.path.expanduser(str(path))
    try:
        try:
            data = _cott_fixture_read(path)
        except CottContractViolation as error:
            if error.message == "fixture adapters are inactive":
                if not os.path.exists(expanded):
                    parent = os.path.dirname(expanded)
                    if parent:
                        os.makedirs(parent, exist_ok=True)
                    with open(expanded, "wb") as handle:
                        handle.write(PGCLI_DEFAULT_CONFIG.encode("utf-8"))
                with open(expanded, "rb") as handle:
                    data = handle.read()
            elif isinstance(error.__cause__, FileNotFoundError):
                _cott_fixture_write(path, PGCLI_DEFAULT_CONFIG.encode("utf-8"))
                data = _cott_fixture_read(path)
            else:
                raise
    except CottContractViolation as error:
        if isinstance(error.__cause__, OSError):
            return Err(error=ConfigError_Unreadable(path=expanded, message=str(error.__cause__)))
        raise
    except OSError as error:
        return Err(error=ConfigError_Unreadable(path=expanded, message=str(error)))
    return parse_pgcli_config(data.decode("utf-8"))
