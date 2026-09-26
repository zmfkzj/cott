import re
from typing import Final

from cott_runtime import CottList, Err, FrozenMap, Ok, Option, Result, Some

from real.harlequin.config_types import ConfigEntry, ConfigError, ConfigError_Invalid, ConfigValue, ConfigValue_Array, ConfigValue_Table, ConfigValue_Text, Profile

_NAME_PATTERN: Final[str] = "[A-Za-z_][A-Za-z0-9_]*"
_TITLE: Final[str] = "Harlequin couldn't load your config file."


def _missing(name: str, path: str, source: Option[str]) -> Result[str, ConfigError]:
    message = (
        f"Config file reads the environment variable {name}, which is not set. "
        f"Set it, or write ${{{name}:-a default}} to say what to use when it is not, at {path}."
    )
    if isinstance(source, Some):
        message += f"\nFound in the config file at {source.value}."
    return Err(error=ConfigError_Invalid(title=_TITLE, message=message))


def _expand(text: str, environment: FrozenMap[str, str], path: str, source: Option[str]) -> Result[str, ConfigError]:
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith("$${", i):
            out.append("${")
            i += 3
            continue
        if text.startswith("${", i):
            end = text.find("}", i + 2)
            if end >= 0:
                inner = text[i + 2 : end]
                sep = inner.find(":-")
                name = inner if sep < 0 else inner[:sep]
                if re.fullmatch(_NAME_PATTERN, name) is not None:
                    value = environment.get(name, "")
                    if value != "":
                        out.append(value)
                    elif sep >= 0:
                        out.append(inner[sep + 2 :])
                    else:
                        return _missing(name, path, source)
                    i = end + 1
                    continue
        out.append(text[i])
        i += 1
    return Ok(value="".join(out))


def _value(value: ConfigValue, environment: FrozenMap[str, str], path: str, source: Option[str]) -> Result[ConfigValue, ConfigError]:
    if isinstance(value, ConfigValue_Text):
        expanded = _expand(value.value, environment, path, source)
        if isinstance(expanded, Err):
            return Err(error=expanded.error)
        return Ok(value=ConfigValue_Text(value=expanded.value))
    if isinstance(value, ConfigValue_Array):
        items: list[ConfigValue] = []
        for index, item in enumerate(value.values):
            converted = _value(item, environment, f"{path}[{index}]", source)
            if isinstance(converted, Err):
                return Err(error=converted.error)
            items.append(converted.value)
        return Ok(value=ConfigValue_Array(values=CottList(values=items)))
    if isinstance(value, ConfigValue_Table):
        entries = _entries(value.entries, environment, path, source)
        if isinstance(entries, Err):
            return Err(error=entries.error)
        return Ok(value=ConfigValue_Table(entries=entries.value))
    return Ok(value=value)


def _entries(entries: CottList[ConfigEntry], environment: FrozenMap[str, str], prefix: str, source: Option[str]) -> Result[CottList[ConfigEntry], ConfigError]:
    result: list[ConfigEntry] = []
    for entry in entries:
        converted = _value(entry.value, environment, f"{prefix}.{entry.key}", source)
        if isinstance(converted, Err):
            return Err(error=converted.error)
        result.append(ConfigEntry(key=entry.key, value=converted.value))
    return Ok(value=CottList(values=result))


def interpolate_profile(profile: Profile, environment: FrozenMap[str, str], source: Option[str]) -> Result[Profile, ConfigError]:
    entries = _entries(profile.entries, environment, f"profiles.{profile.name}", source)
    if isinstance(entries, Err):
        return Err(error=entries.error)
    return Ok(value=Profile(name=profile.name, entries=entries.value))
