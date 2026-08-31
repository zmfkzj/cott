import tomllib
from pathlib import Path
from typing import cast

from cott_runtime import CottList, Err, Nothing, Ok, Result, Some
from real.harlequin.core_types import (
    AdapterKind,
    AdapterKind_Adbc,
    AdapterKind_BigQuery,
    AdapterKind_Cassandra,
    AdapterKind_Databricks,
    AdapterKind_DuckDb,
    AdapterKind_MySql,
    AdapterKind_NebulaGraph,
    AdapterKind_Odbc,
    AdapterKind_PostgreSql,
    AdapterKind_Sqlite,
    AdapterKind_Trino,
    Configuration,
    ConfigurationError,
    ConfigurationError_Invalid,
    ConfigurationError_Missing,
    ConfigurationError_ProfileDuplicate,
    ConnectionProfile,
    Setting,
)


def load_configuration(path: Path) -> Result[Configuration, ConfigurationError]:
    if not path.exists():
        return Err(error=ConfigurationError_Missing(path=path))

    document = cast(dict[str, object], tomllib.loads(path.read_text(encoding="utf-8")))
    raw_profiles = cast(list[object], document.get("profiles", []))
    if len(raw_profiles) > 100000:
        return Err(error=ConfigurationError_Invalid(path=path, message="configuration contains more than 100000 profiles"))

    profiles: list[ConnectionProfile] = []
    profile_names: set[str] = set()
    for raw_profile in raw_profiles:
        profile = cast(dict[str, object], raw_profile)
        name = str(profile.get("name", ""))
        if name in profile_names:
            return Err(error=ConfigurationError_ProfileDuplicate(name=name))
        profile_names.add(name)

        adapter_name = str(profile.get("adapter", "duckdb")).lower()
        adapter: AdapterKind
        if adapter_name == "duckdb":
            adapter = AdapterKind_DuckDb()
        elif adapter_name == "sqlite":
            adapter = AdapterKind_Sqlite()
        elif adapter_name == "postgresql" or adapter_name == "postgres":
            adapter = AdapterKind_PostgreSql()
        elif adapter_name == "mysql":
            adapter = AdapterKind_MySql()
        elif adapter_name == "odbc":
            adapter = AdapterKind_Odbc()
        elif adapter_name == "bigquery":
            adapter = AdapterKind_BigQuery()
        elif adapter_name == "trino":
            adapter = AdapterKind_Trino()
        elif adapter_name == "databricks":
            adapter = AdapterKind_Databricks()
        elif adapter_name == "adbc":
            adapter = AdapterKind_Adbc()
        elif adapter_name == "cassandra":
            adapter = AdapterKind_Cassandra()
        elif adapter_name == "nebulagraph" or adapter_name == "nebula":
            adapter = AdapterKind_NebulaGraph()
        else:
            return Err(error=ConfigurationError_Invalid(path=path, message=f"unknown adapter: {adapter_name}"))

        raw_settings = cast(list[object], profile.get("settings", []))
        settings: list[Setting] = []
        for raw_setting in raw_settings:
            setting = cast(dict[str, object], raw_setting)
            settings.append(Setting(name=str(setting.get("name", "")), value=str(setting.get("value", ""))))

        profiles.append(
            ConnectionProfile(
                name=name,
                adapter=adapter,
                endpoint=str(profile.get("endpoint", "")),
                settings=CottList(values=settings),
                read_only=bool(profile.get("read_only", False)),
            )
        )

    if "default_profile" in document:
        default_profile = Some(value=str(document["default_profile"]))
    else:
        default_profile = Nothing()

    return Ok(
        value=Configuration(
            profiles=CottList(values=profiles),
            default_profile=default_profile,
            theme=str(document.get("theme", "harlequin")),
            keymap=str(document.get("keymap", "default")),
        )
    )
