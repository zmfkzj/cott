import json
from decimal import Decimal
from typing import Final, cast

from cott_runtime import CottContractViolation, CottList, Err, Ok, Result, _cott_fixture_read

from frogmouth.config import default_config
from frogmouth.config_types import Config, Dock, Dock_Left, Dock_Right, Theme, Theme_Dark, Theme_Light
from frogmouth.storage import save_config
from frogmouth.storage_types import LoadedConfig, StoreError, StoreError_Malformed, StoreError_ReadFailed

_FILE_NAME: Final[str] = "configuration.json"
_INACTIVE_ADAPTERS: Final[str] = "fixture adapters are inactive"


def _read_host(path: str) -> bytes | None:
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except (FileNotFoundError, NotADirectoryError):
        return None


def _read_bytes(path: str) -> bytes | None:
    """Content of the file at path, or None when it does not exist.

    Reads the active fs fixture, otherwise the host file system. Every other
    failure raises OSError, ValueError or CottContractViolation.
    """
    try:
        return _cott_fixture_read(path)
    except CottContractViolation as violation:
        if violation.message == _INACTIVE_ADAPTERS:
            return _read_host(path)
        if isinstance(violation.__cause__, (FileNotFoundError, NotADirectoryError)):
            return None
        raise
    except (FileNotFoundError, NotADirectoryError):
        # Injected fixture failures at file.open and file.read are raised directly, not as a cause.
        return None


def _has_constant(document: object) -> bool:
    """Whether the parsed document holds NaN/Infinity; JSON numbers parse to Decimal, so any float is one."""
    pending: list[object] = [document]
    while pending:
        value = pending.pop()
        if isinstance(value, float):
            return True
        if isinstance(value, dict):
            pending.extend(cast(dict[str, object], value).values())
        elif isinstance(value, list):
            pending.extend(cast(list[object], value))
    return False


def _extensions(value: object) -> CottList[str] | None:
    """The markdown extensions a JSON array of strings denotes, in order; None for any other value."""
    if not isinstance(value, list):
        return None
    values: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str):
            return None
        values.append(item)
    return CottList(values=values)


def load_config(config_directory: str) -> Result[LoadedConfig, StoreError]:
    path = config_directory + "/" + _FILE_NAME
    try:
        data = _read_bytes(path)
    except (OSError, ValueError, CottContractViolation) as error:
        return Err(error=StoreError_ReadFailed(path=path, message=str(error)))
    defaults = default_config()
    if data is None:
        saved = save_config(config_directory, defaults)
        if isinstance(saved, Err):
            return saved
        return Ok(value=LoadedConfig(path=path, config=defaults))
    try:
        # Decimal has no digit limit, so an oversized number under an ignored key cannot reject the document.
        document: object = json.loads(data.decode("utf-8"), parse_int=Decimal, parse_float=Decimal)
    except (ValueError, RecursionError) as error:
        return Err(error=StoreError_Malformed(path=path, message=str(error)))
    if _has_constant(document):
        return Err(error=StoreError_Malformed(path=path, message="NaN and Infinity are not JSON values"))
    if not isinstance(document, dict):
        return Err(error=StoreError_Malformed(path=path, message="configuration is not a JSON object"))
    settings = cast(dict[str, object], document)
    theme: Theme = defaults.theme
    markdown_extensions: CottList[str] = defaults.markdown_extensions
    navigation_dock: Dock = defaults.navigation_dock
    if "light_mode" in settings:
        light_mode = settings["light_mode"]
        if not isinstance(light_mode, bool):
            return Err(error=StoreError_Malformed(path=path, message='"light_mode" is not a boolean'))
        theme = Theme_Light() if light_mode else Theme_Dark()
    if "markdown_extensions" in settings:
        extensions = _extensions(settings["markdown_extensions"])
        if extensions is None:
            return Err(error=StoreError_Malformed(path=path, message='"markdown_extensions" is not an array of strings'))
        markdown_extensions = extensions
    if "navigation_left" in settings:
        navigation_left = settings["navigation_left"]
        if not isinstance(navigation_left, bool):
            return Err(error=StoreError_Malformed(path=path, message='"navigation_left" is not a boolean'))
        navigation_dock = Dock_Left() if navigation_left else Dock_Right()
    config = Config(theme=theme, markdown_extensions=markdown_extensions, navigation_dock=navigation_dock)
    return Ok(value=LoadedConfig(path=path, config=config))
