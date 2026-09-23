import pathlib
import tomllib
from typing import Final, cast

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.harlequin.core_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_PostgreSql, AdapterKind_Sqlite, AdapterKind_Trino, Configuration, ConfigurationError, ConfigurationError_Invalid, ConfigurationError_Missing, ConfigurationError_ProfileDuplicate, ConnectionProfile, Setting

_MAX_PROFILES: Final[int] = 100000
_DEFAULT_THEME: Final[str] = "harlequin"
_DEFAULT_KEYMAP: Final[str] = "vscode"


def _adapter(name: str) -> AdapterKind | None:
    key = name.strip().lower().replace("_", "").replace("-", "")
    if key == "duckdb":
        return AdapterKind_DuckDb()
    if key == "sqlite":
        return AdapterKind_Sqlite()
    if key in ("postgresql", "postgres"):
        return AdapterKind_PostgreSql()
    if key == "mysql":
        return AdapterKind_MySql()
    if key == "odbc":
        return AdapterKind_Odbc()
    if key == "bigquery":
        return AdapterKind_BigQuery()
    if key == "trino":
        return AdapterKind_Trino()
    if key == "databricks":
        return AdapterKind_Databricks()
    if key == "adbc":
        return AdapterKind_Adbc()
    if key == "cassandra":
        return AdapterKind_Cassandra()
    if key in ("nebulagraph", "nebula"):
        return AdapterKind_NebulaGraph()
    return None


def _settings(value: object) -> list[Setting] | str:
    result: list[Setting] = []
    seen: set[str] = set()
    if isinstance(value, dict):
        table = cast(dict[str, object], value)
        for name, item in table.items():
            if not isinstance(item, str):
                return "setting values must be strings"
            seen.add(name)
            result.append(Setting(name=name, value=item))
        return result
    if isinstance(value, list):
        items = cast(list[object], value)
        for entry in items:
            if not isinstance(entry, dict):
                return "settings entries must be tables"
            row = cast(dict[str, object], entry)
            if set(row.keys()) != {"name", "value"}:
                return "settings entries require exactly name and value"
            name = row["name"]
            text = row["value"]
            if not isinstance(name, str) or not isinstance(text, str):
                return "setting name and value must be strings"
            if name in seen:
                return "duplicate setting name"
            seen.add(name)
            result.append(Setting(name=name, value=text))
        return result
    return "settings must be a table or array of tables"


def _profile(entry: object, fallback_name: str | None) -> ConnectionProfile | str:
    if not isinstance(entry, dict):
        return "profile must be a table"
    table = cast(dict[str, object], entry)
    allowed = {"name", "adapter", "endpoint", "settings", "read_only"}
    for key in table.keys():
        if key not in allowed:
            return "unknown profile key"
    name_value = table.get("name", fallback_name)
    if not isinstance(name_value, str) or not name_value:
        return "profile name must be a nonempty string"
    if fallback_name is not None and name_value != fallback_name:
        return "profile name does not match its table key"
    adapter_value = table.get("adapter")
    if not isinstance(adapter_value, str):
        return "profile adapter must be a string"
    adapter = _adapter(adapter_value)
    if adapter is None:
        return "unknown profile adapter"
    endpoint = table.get("endpoint")
    if not isinstance(endpoint, str):
        return "profile endpoint must be a string"
    read_only = table.get("read_only", False)
    if not isinstance(read_only, bool):
        return "profile read_only must be a boolean"
    settings = _settings(table.get("settings", {}))
    if isinstance(settings, str):
        return settings
    return ConnectionProfile(name=name_value, adapter=adapter, endpoint=endpoint, settings=CottList(values=settings), read_only=read_only)


def load_configuration(path: pathlib.Path) -> Result[Configuration, ConfigurationError]:
    try:
        with open(path, "rb") as handle:
            document = cast(dict[str, object], tomllib.load(handle))
    except FileNotFoundError:
        return Err(error=ConfigurationError_Missing(path=path))
    except tomllib.TOMLDecodeError:
        return Err(error=ConfigurationError_Invalid(path=path, message="malformed TOML"))
    except UnicodeDecodeError:
        return Err(error=ConfigurationError_Invalid(path=path, message="malformed TOML"))
    except OSError:
        return Err(error=ConfigurationError_Invalid(path=path, message="configuration file could not be read"))
    for key in document.keys():
        if key not in ("profiles", "default_profile", "theme", "keymap"):
            return Err(error=ConfigurationError_Invalid(path=path, message="unknown configuration key"))
    raw_profiles = document.get("profiles", [])
    entries: list[tuple[object, str | None]] = []
    if isinstance(raw_profiles, list):
        items = cast(list[object], raw_profiles)
        for item in items:
            entries.append((item, None))
    elif isinstance(raw_profiles, dict):
        named = cast(dict[str, object], raw_profiles)
        for name, item in named.items():
            entries.append((item, name))
    else:
        return Err(error=ConfigurationError_Invalid(path=path, message="profiles must be an array or table"))
    if len(entries) > _MAX_PROFILES:
        return Err(error=ConfigurationError_Invalid(path=path, message="too many profiles"))
    profiles: list[ConnectionProfile] = []
    seen: set[str] = set()
    for item, fallback in entries:
        profile = _profile(item, fallback)
        if isinstance(profile, str):
            return Err(error=ConfigurationError_Invalid(path=path, message=profile))
        if profile.name in seen:
            return Err(error=ConfigurationError_ProfileDuplicate(name=profile.name))
        seen.add(profile.name)
        profiles.append(profile)
    default_value = document.get("default_profile")
    if default_value is not None and not isinstance(default_value, str):
        return Err(error=ConfigurationError_Invalid(path=path, message="default_profile must be a string"))
    if isinstance(default_value, str) and default_value not in seen:
        return Err(error=ConfigurationError_Invalid(path=path, message="default_profile names no defined profile"))
    theme = document.get("theme", _DEFAULT_THEME)
    keymap = document.get("keymap", _DEFAULT_KEYMAP)
    if not isinstance(theme, str) or not isinstance(keymap, str):
        return Err(error=ConfigurationError_Invalid(path=path, message="theme and keymap must be strings"))
    default_profile = Some(value=default_value) if isinstance(default_value, str) else Nothing()
    return Ok(value=Configuration(profiles=CottList(values=profiles), default_profile=default_profile, theme=theme, keymap=keymap))
