import pathlib
import tomllib
from typing import Final, cast

from cott_runtime import CottContractViolation, CottList, Err, Nothing, Ok, Result, Some, _cott_fixture_read
from real.harlequin.core_types import AdapterKind, AdapterKind_Adbc, AdapterKind_BigQuery, AdapterKind_Cassandra, AdapterKind_Databricks, AdapterKind_DuckDb, AdapterKind_MySql, AdapterKind_NebulaGraph, AdapterKind_Odbc, AdapterKind_PostgreSql, AdapterKind_Sqlite, AdapterKind_Trino, Configuration, ConfigurationError, ConfigurationError_Invalid, ConfigurationError_Missing, ConfigurationError_ProfileDuplicate, ConnectionProfile, Setting

_DEFAULT_THEME: Final[str] = "harlequin"
_DEFAULT_KEYMAP: Final[str] = "default"
_INACTIVE: Final[str] = "fixture adapters are inactive"
_UNREADABLE: Final[str] = "configuration file could not be read"


def _ascii_lower(text: str) -> str:
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)


def _adapter(label: str) -> AdapterKind | None:
    key = _ascii_lower(label)
    if key == "duckdb":
        return AdapterKind_DuckDb()
    if key == "sqlite":
        return AdapterKind_Sqlite()
    if key in ("postgres", "postgresql"):
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
    if key == "nebula":
        return AdapterKind_NebulaGraph()
    return None


def _profile(entry: object) -> ConnectionProfile | str:
    if not isinstance(entry, dict):
        return "profiles entries must be tables"
    table = cast(dict[str, object], entry)
    for key in table.keys():
        if key not in ("name", "adapter", "connection", "read_only", "settings"):
            return f"unknown profile key {key!r}"
    if "name" not in table:
        return "missing required profile key name"
    name = table["name"]
    if not isinstance(name, str):
        return "profile key name must be a string"
    if "adapter" not in table:
        return "missing required profile key adapter"
    adapter_value = table["adapter"]
    if not isinstance(adapter_value, str):
        return "profile key adapter must be a string"
    adapter = _adapter(adapter_value)
    if adapter is None:
        return "profile key adapter names no known adapter"
    if "connection" not in table:
        return "missing required profile key connection"
    connection = table["connection"]
    if not isinstance(connection, str):
        return "profile key connection must be a string"
    read_only = table.get("read_only", False)
    if not isinstance(read_only, bool):
        return "profile key read_only must be a boolean"
    settings: list[Setting] = []
    if "settings" in table:
        raw_settings = table["settings"]
        if not isinstance(raw_settings, dict):
            return "profile key settings must be a table"
        settings_table = cast(dict[str, object], raw_settings)
        for setting_name, setting_value in settings_table.items():
            if not isinstance(setting_value, str):
                return f"profile settings key {setting_name!r} must be a string"
            settings.append(Setting(name=setting_name, value=setting_value))
    return ConnectionProfile(name=name, adapter=adapter, endpoint=connection, settings=CottList(values=settings), read_only=read_only)


def _read(path: pathlib.Path) -> bytes | ConfigurationError:
    try:
        return _cott_fixture_read(path)
    except CottContractViolation as violation:
        if violation.message != _INACTIVE:
            if isinstance(violation.__cause__, FileNotFoundError):
                return ConfigurationError_Missing(path=path)
            return ConfigurationError_Invalid(path=path, message=_UNREADABLE)
    except FileNotFoundError:
        return ConfigurationError_Missing(path=path)
    except OSError:
        return ConfigurationError_Invalid(path=path, message=_UNREADABLE)
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return ConfigurationError_Missing(path=path)
    except OSError:
        return ConfigurationError_Invalid(path=path, message=_UNREADABLE)


def load_configuration(path: pathlib.Path) -> Result[Configuration, ConfigurationError]:
    data = _read(path)
    if not isinstance(data, bytes):
        return Err(error=data)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return Err(error=ConfigurationError_Invalid(path=path, message="invalid UTF-8"))
    try:
        document = cast(dict[str, object], tomllib.loads(text))
    except tomllib.TOMLDecodeError:
        return Err(error=ConfigurationError_Invalid(path=path, message="invalid TOML"))
    for key in document.keys():
        if key not in ("default_profile", "theme", "keymap", "profiles"):
            return Err(error=ConfigurationError_Invalid(path=path, message=f"unknown top-level key {key!r}"))
    default_value = document.get("default_profile")
    if default_value is not None and not isinstance(default_value, str):
        return Err(error=ConfigurationError_Invalid(path=path, message="default_profile must be a string"))
    theme = document.get("theme", _DEFAULT_THEME)
    if not isinstance(theme, str):
        return Err(error=ConfigurationError_Invalid(path=path, message="theme must be a string"))
    keymap = document.get("keymap", _DEFAULT_KEYMAP)
    if not isinstance(keymap, str):
        return Err(error=ConfigurationError_Invalid(path=path, message="keymap must be a string"))
    raw_profiles = document.get("profiles", [])
    if not isinstance(raw_profiles, list):
        return Err(error=ConfigurationError_Invalid(path=path, message="profiles must be an array of tables"))
    entries = cast(list[object], raw_profiles)
    profiles: list[ConnectionProfile] = []
    seen: set[str] = set()
    for entry in entries:
        profile = _profile(entry)
        if isinstance(profile, str):
            return Err(error=ConfigurationError_Invalid(path=path, message=profile))
        if profile.name in seen:
            return Err(error=ConfigurationError_ProfileDuplicate(name=profile.name))
        seen.add(profile.name)
        profiles.append(profile)
    default_profile = Some(value=default_value) if isinstance(default_value, str) else Nothing()
    return Ok(value=Configuration(profiles=CottList(values=profiles), default_profile=default_profile, theme=theme, keymap=keymap))
