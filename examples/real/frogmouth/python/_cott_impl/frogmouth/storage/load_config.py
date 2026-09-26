import json
from typing import cast

from cott_runtime import CottContractViolation, CottList, Err, Ok, Result, _cott_fixture_read

from frogmouth.config import default_config
from frogmouth.config_types import Config, Dock, Dock_Left, Dock_Right, Theme, Theme_Dark, Theme_Light
from frogmouth.storage import save_config
from frogmouth.storage_types import LoadedConfig, StoreError, StoreError_Malformed, StoreError_ReadFailed


def _read_bytes(path: str) -> bytes | None:
    try:
        return _cott_fixture_read(path)
    except CottContractViolation as error:
        cause = error.__cause__
        if cause is None and error.message == "fixture adapters are inactive":
            try:
                with open(path, "rb") as handle:
                    return handle.read()
            except (FileNotFoundError, NotADirectoryError):
                return None
        if isinstance(cause, (FileNotFoundError, NotADirectoryError)):
            return None
        raise


def _string_list(value: object) -> list[str] | None:
    if not isinstance(value, list):
        return None
    result: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str):
            return None
        result.append(item)
    return result


def load_config(config_directory: str) -> Result[LoadedConfig, StoreError]:
    path = config_directory + "/configuration.json"
    try:
        data = _read_bytes(path)
    except (OSError, CottContractViolation) as error:
        return Err(error=StoreError_ReadFailed(path=path, message=str(error)))
    if data is None:
        defaults = default_config()
        saved = save_config(config_directory, defaults)
        if isinstance(saved, Err):
            return saved
        return Ok(value=LoadedConfig(path=path, config=defaults))
    try:
        # int() raises ValueError for NaN/Infinity, rejecting non-standard JSON constants.
        parsed: object = json.loads(data.decode("utf-8", errors="strict"), parse_constant=int)
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        return Err(error=StoreError_Malformed(path=path, message=str(error)))
    if not isinstance(parsed, dict):
        return Err(error=StoreError_Malformed(path=path, message="configuration is not a JSON object"))
    document = cast(dict[str, object], parsed)
    defaults = default_config()
    theme: Theme = defaults.theme
    extensions: CottList[str] = defaults.markdown_extensions
    dock: Dock = defaults.navigation_dock
    if "light_mode" in document:
        light = document["light_mode"]
        if not isinstance(light, bool):
            return Err(error=StoreError_Malformed(path=path, message="light_mode must be a boolean"))
        theme = Theme_Light() if light else Theme_Dark()
    if "markdown_extensions" in document:
        values = _string_list(document["markdown_extensions"])
        if values is None:
            return Err(error=StoreError_Malformed(path=path, message="markdown_extensions must be an array of strings"))
        extensions = CottList(values=values)
    if "navigation_left" in document:
        left = document["navigation_left"]
        if not isinstance(left, bool):
            return Err(error=StoreError_Malformed(path=path, message="navigation_left must be a boolean"))
        dock = Dock_Left() if left else Dock_Right()
    config = Config(theme=theme, markdown_extensions=extensions, navigation_dock=dock)
    return Ok(value=LoadedConfig(path=path, config=config))
