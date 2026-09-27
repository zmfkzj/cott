import datetime
import pathlib
import tomllib
from typing import cast

from cott_runtime import CottContractViolation, CottList, Err, Nothing, Ok, Option, Result, Some, _cott_fixture_read
from real.harlequin.config_types import ConfigEntry, ConfigError, ConfigError_Invalid, ConfigFile, ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Integer, ConfigValue_Real, ConfigValue_Table, ConfigValue_Text, Profile
from real.harlequin.keymap_types import KeyBinding, KeyMap


def _fail(title: str, message: str) -> Result[Option[ConfigFile], ConfigError]:
    return Err(error=ConfigError_Invalid(title=title, message=message))


def _type_name(value: object) -> str:
    if isinstance(value, dict):
        return "table"
    if isinstance(value, str):
        return "string"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, datetime.datetime):
        return "datetime"
    if isinstance(value, datetime.date):
        return "date"
    if isinstance(value, datetime.time):
        return "time"
    return "nothing"


def _type_error(expected: str, value: object, key: str, path: str) -> Result[Option[ConfigFile], ConfigError]:
    return _fail("Harlequin couldn't load your config file.", f"Expected `{expected}`, got `{_type_name(value)}` at {key}.\nFound in the config file at {path}.")


def _convert(value: object) -> ConfigValue:
    if isinstance(value, str):
        return ConfigValue_Text(value=value)
    if isinstance(value, bool):
        return ConfigValue_Boolean(value=value)
    if isinstance(value, int):
        return ConfigValue_Integer(value=value)
    if isinstance(value, float):
        return ConfigValue_Real(value=value)
    if isinstance(value, list):
        items = cast(list[object], value)
        return ConfigValue_Array(values=CottList(values=[_convert(item) for item in items]))
    if isinstance(value, dict):
        return ConfigValue_Table(entries=_entries(cast(dict[str, object], value)))
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return ConfigValue_Text(value=value.isoformat())
    return ConfigValue_Text(value=str(value))


def _entries(table: dict[str, object]) -> CottList[ConfigEntry]:
    return CottList(values=[ConfigEntry(key=key, value=_convert(value)) for key, value in table.items()])


def _read_bytes(path: pathlib.Path) -> Option[bytes]:
    try:
        return Some(value=_cott_fixture_read(path))
    except CottContractViolation as violation:
        if violation.message != "fixture adapters are inactive":
            cause = violation.__cause__
            if isinstance(cause, FileNotFoundError):
                return Nothing()
            if isinstance(cause, OSError):
                return Some(value=b"")
            raise
    except FileNotFoundError:
        return Nothing()
    except OSError:
        return Some(value=b"")
    try:
        return Some(value=path.read_bytes())
    except FileNotFoundError:
        return Nothing()
    except OSError:
        return Some(value=b"")


def read_config_file(path: pathlib.Path) -> Result[Option[ConfigFile], ConfigError]:
    raw = _read_bytes(path)
    if not isinstance(raw, Some):
        return Ok(value=Nothing())
    text_path = str(path)
    try:
        document = cast(dict[str, object], tomllib.loads(raw.value.decode("utf-8")))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        return _fail("Harlequin could not load the config file.", f"Attempted to load the config file at {text_path}, but encountered an error:\n\n{error}")
    config: dict[str, object] = document
    if path.name == "pyproject.toml":
        tool = document.get("tool")
        section: object = cast(dict[str, object], tool).get("harlequin") if isinstance(tool, dict) else None
        config = cast(dict[str, object], section) if isinstance(section, dict) else {}
    for key in config:
        if key not in ("default_profile", "profiles", "keymaps"):
            return _fail("Harlequin couldn't load your config file.", f"Found unexpected key in config: {key}\nFound in the config file at {text_path}.")
    default: Option[str] = Nothing()
    if "default_profile" in config:
        value = config["default_profile"]
        if not isinstance(value, str):
            return _type_error("string", value, "default_profile", text_path)
        default = Some(value=value)
    profiles: list[Profile] = []
    if "profiles" in config:
        raw_profiles = config["profiles"]
        if not isinstance(raw_profiles, dict):
            return _type_error("table", raw_profiles, "profiles", text_path)
        for name, body in cast(dict[str, object], raw_profiles).items():
            if not isinstance(body, dict):
                return _type_error("table", body, f"profiles.{name}", text_path)
            if name == "None":
                return _fail("Harlequin couldn't load your config file.", f"Config file defines a profile named 'None', which is not allowed\nFound in the config file at {text_path}.")
            profiles.append(Profile(name=name, entries=_entries(cast(dict[str, object], body))))
    keymaps: list[KeyMap] = []
    if "keymaps" in config:
        raw_maps = config["keymaps"]
        if not isinstance(raw_maps, dict):
            return _type_error("table", raw_maps, "keymaps", text_path)
        for map_name, bindings in cast(dict[str, object], raw_maps).items():
            if not isinstance(bindings, list):
                return _type_error("array", bindings, f"keymaps.{map_name}", text_path)
            parsed: list[KeyBinding] = []
            for index, binding in enumerate(cast(list[object], bindings)):
                where = f"keymaps.{map_name}[{index}]"
                if not isinstance(binding, dict):
                    return _type_error("table", binding, where, text_path)
                fields = cast(dict[str, object], binding)
                for prop in fields:
                    if prop not in ("keys", "action", "key_display"):
                        return _fail("Harlequin could not load your keymap.", f"Key bindings must be defined in config files with only three properties: `keys`, `action`, and `key_profile`. Got a binding in the map named {map_name} that tried to define a property: '{prop}'")
                keys = fields.get("keys")
                action = fields.get("action")
                if not isinstance(keys, str):
                    return _type_error("string", keys, f"{where}.keys", text_path)
                if not isinstance(action, str):
                    return _type_error("string", action, f"{where}.action", text_path)
                display: Option[str] = Nothing()
                if "key_display" in fields:
                    shown = fields["key_display"]
                    if not isinstance(shown, str):
                        return _type_error("string", shown, f"{where}.key_display", text_path)
                    display = Some(value=shown)
                parsed.append(KeyBinding(keys=keys, action=action, key_display=display))
            keymaps.append(KeyMap(name=map_name, bindings=CottList(values=parsed)))
    defines = isinstance(default, Some) or bool(profiles) or bool(keymaps)
    return Ok(value=Some(value=ConfigFile(path=text_path, default_profile=default, profiles=CottList(values=profiles), keymaps=CottList(values=keymaps), defines_anything=defines)))
