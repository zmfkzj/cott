import logging
import os
import pathlib
from typing import Final

from cott_runtime import Err, Ok, Result
from real.pgcli.config_types import ConfigError, ConfigError_Invalid, ConfigError_Unreadable

_FORMAT: Final[str] = "%(asctime)s (%(process)d/%(threadName)s) %(name)s %(levelname)s - %(message)s"


def configure_pgcli_logging(log_file: str, log_level: str, config_directory: str) -> Result[str, ConfigError]:
    if log_file == "default":
        log_path = config_directory + "log"
    else:
        log_path = os.path.expanduser(log_file)
    level_name = log_level.upper()
    levels: dict[str, int] = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NONE": logging.CRITICAL,
    }
    if level_name not in levels:
        return Err(error=ConfigError_Invalid(message="Unknown log level: " + log_level))
    try:
        pathlib.Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler
        if level_name == "NONE":
            handler = logging.NullHandler()
        else:
            handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        handler.setFormatter(logging.Formatter(_FORMAT))
        level = levels[level_name]
        for name in ("pgcli", "pgspecial"):
            logger = logging.getLogger(name)
            logger.addHandler(handler)
            logger.setLevel(level)
        pgcli_logger = logging.getLogger("pgcli")
        pgcli_logger.debug("Initializing pgcli logging.")
        pgcli_logger.debug("Log file %r.", log_path)
    except OSError as error:
        return Err(error=ConfigError_Unreadable(path=log_path, message=str(error)))
    return Ok(value=log_path)
