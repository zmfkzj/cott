from collections.abc import MutableMapping
from pathlib import Path
from typing import cast
import os
import tempfile

import tomlkit
from tomlkit.exceptions import TOMLKitError

from cott_runtime import CottContractViolation, Err, Ok, Option, Result, Some, _cott_fixture_read, _cott_fixture_replace
from real.harlequin.config_types import ConfigError, ConfigError_Invalid, ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Integer, ConfigValue_Real, ConfigValue_Text, Profile


def _create_error(message: str) -> Err[ConfigError]:
    return Err(error=ConfigError_Invalid(title="Harlequin could not create your configuration.", message=message))


def _load_error(path: Path, error: Exception) -> Err[ConfigError]:
    return Err(error=ConfigError_Invalid(title="Harlequin could not load the config file.", message=f"Attempted to load the config file at {path}, but encountered an error:\n\n{error}"))


def _violation_text(error: CottContractViolation) -> str:
    cause = error.__cause__
    if isinstance(cause, OSError):
        return str(cause)
    return error.message


def _plain(value: ConfigValue) -> object:
    if isinstance(value, ConfigValue_Text):
        return value.value
    if isinstance(value, ConfigValue_Integer):
        return value.value
    if isinstance(value, ConfigValue_Real):
        return value.value
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


def _remove_temporary(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        return


def write_profile(path: Path, profile: Profile, default_profile: Option[str]) -> Result[Path, ConfigError]:
    fixture = True
    try:
        raw: bytes | None = _cott_fixture_read(path)
    except CottContractViolation as error:
        if error.message == "fixture adapters are inactive":
            fixture = False
            try:
                raw = path.read_bytes()
            except FileNotFoundError:
                raw = None
            except OSError as read_error:
                return _create_error(str(read_error))
        elif isinstance(error.__cause__, FileNotFoundError):
            raw = None
        else:
            return _create_error(_violation_text(error))
    except FileNotFoundError:
        raw = None
    except OSError as error:
        return _create_error(str(error))

    try:
        document = tomlkit.parse(raw.decode("utf-8")) if raw is not None else tomlkit.document()
    except (TOMLKitError, UnicodeDecodeError) as error:
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
            _cott_fixture_replace(path, data)
        except CottContractViolation as error:
            return _create_error(_violation_text(error))
        except OSError as error:
            return _create_error(str(error))
        return Ok(value=path)

    temporary: str | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = stream.name
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as error:
        return _create_error(str(error))
    finally:
        if temporary is not None:
            _remove_temporary(temporary)
    return Ok(value=path)
