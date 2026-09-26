from collections.abc import MutableMapping
from pathlib import Path
from typing import Final, cast

import tomlkit
from tomlkit.exceptions import TOMLKitError
from cott_runtime import CottContractViolation, Err, Ok, Option, Result, Some, _cott_fixture_read, _cott_fixture_write
from real.harlequin.config_types import ConfigError, ConfigError_Invalid, ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Integer, ConfigValue_Real, ConfigValue_Text, Profile

_LOAD_TITLE: Final[str] = "Harlequin could not load the config file."
_CREATE_TITLE: Final[str] = "Harlequin could not create your configuration."
_INACTIVE: Final[str] = "fixture adapters are inactive"


def _create_error(message: str) -> Result[Path, ConfigError]:
    return Err(error=ConfigError_Invalid(title=_CREATE_TITLE, message=message))


def _load_error(path: Path, error: Exception) -> Result[Path, ConfigError]:
    return Err(error=ConfigError_Invalid(title=_LOAD_TITLE, message=f"Attempted to load the config file at {path}, but encountered an error:\n\n{error}"))


def _violation_text(error: CottContractViolation) -> str:
    cause = error.__cause__
    if isinstance(cause, OSError):
        return str(cause)
    return error.message


def _plain(value: ConfigValue) -> object:
    if isinstance(value, ConfigValue_Text):
        return value.value
    if isinstance(value, ConfigValue_Integer):
        return int(value.value)
    if isinstance(value, ConfigValue_Real):
        return float(value.value)
    if isinstance(value, ConfigValue_Boolean):
        return value.value
    if isinstance(value, ConfigValue_Array):
        return [_plain(item) for item in value.values]
    table: dict[str, object] = {}
    for entry in value.entries:
        table[entry.key] = _plain(entry.value)
    return table


def _child(parent: MutableMapping[str, object], key: str, super_table: bool) -> MutableMapping[str, object]:
    existing = parent.get(key)
    if isinstance(existing, MutableMapping):
        return cast(MutableMapping[str, object], existing)
    created = tomlkit.table(is_super_table=super_table)
    parent[key] = created
    return cast(MutableMapping[str, object], created)


def write_profile(path: Path, profile: Profile, default_profile: Option[str]) -> Result[Path, ConfigError]:
    fixture = True
    text: str | None = None
    try:
        text = _cott_fixture_read(path).decode("utf-8")
    except CottContractViolation as error:
        if error.message == _INACTIVE:
            fixture = False
        elif isinstance(error.__cause__, FileNotFoundError):
            text = None
        else:
            return _create_error(_violation_text(error))
    except OSError as error:
        return _create_error(str(error))
    except UnicodeDecodeError as error:
        return _load_error(path, error)
    if not fixture:
        try:
            text = path.read_text(encoding="utf-8") if path.exists() else None
        except OSError as error:
            return _create_error(str(error))
        except UnicodeDecodeError as error:
            return _load_error(path, error)
    try:
        document = tomlkit.parse(text) if text is not None else tomlkit.document()
    except TOMLKitError as error:
        return _load_error(path, error)
    root = cast(MutableMapping[str, object], document)
    target = root
    if path.name == "pyproject.toml":
        target = _child(_child(root, "tool", True), "harlequin", False)
    if isinstance(default_profile, Some):
        target["default_profile"] = default_profile.value
    elif "default_profile" in target:
        del target["default_profile"]
    profiles = _child(target, "profiles", True)
    table = tomlkit.table()
    for entry in profile.entries:
        table.add(entry.key, _plain(entry.value))
    if profile.name in profiles:
        del profiles[profile.name]
    profiles[profile.name] = table
    data = tomlkit.dumps(document).encode("utf-8")
    if fixture:
        try:
            _cott_fixture_write(path, data)
        except CottContractViolation as error:
            return _create_error(_violation_text(error))
        except OSError as error:
            return _create_error(str(error))
        return Ok(value=path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    except OSError as error:
        return _create_error(str(error))
    return Ok(value=path)
