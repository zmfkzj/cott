import json
import math
import re

from cott_runtime import CottList
from real.harlequin.config_types import ConfigEntry, ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Integer, ConfigValue_Real, ConfigValue_Text, Profile
from real.harlequin.sqltext import redact_connection_string
from real.harlequin.sqltext_types import REDACTED


def _key(key: str) -> str:
    if re.fullmatch("[A-Za-z0-9_-]+", key) is not None:
        return key
    return json.dumps(key, ensure_ascii=False)


def _string(text: str) -> str:
    return json.dumps(text, ensure_ascii=False)


def _is_secret(key: str, secret_keys: CottList[str]) -> bool:
    for name in secret_keys:
        if name == key:
            return True
    return re.search("password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key", key, re.IGNORECASE) is not None


def _real(number: float) -> str:
    if math.isnan(number):
        return "nan"
    if math.isinf(number):
        return "inf" if number > 0 else "-inf"
    return repr(number)


def _value(value: ConfigValue, conn: bool, secret_keys: CottList[str]) -> str:
    if isinstance(value, ConfigValue_Text):
        return _string(redact_connection_string(value.value) if conn else value.value)
    if isinstance(value, ConfigValue_Integer):
        return str(value.value)
    if isinstance(value, ConfigValue_Real):
        return _real(value.value)
    if isinstance(value, ConfigValue_Boolean):
        return "true" if value.value else "false"
    if isinstance(value, ConfigValue_Array):
        return "[" + ", ".join(_value(item, conn, secret_keys) for item in value.values) + "]"
    parts = [_entry(entry, secret_keys) for entry in value.entries]
    return "{" + ", ".join(parts) + "}"


def _entry(entry: ConfigEntry, secret_keys: CottList[str]) -> str:
    if _is_secret(entry.key, secret_keys):
        value = entry.value
        if isinstance(value, ConfigValue_Array):
            rendered = "[" + ", ".join(_string(REDACTED) for _ in value.values) + "]"
        else:
            rendered = _string(REDACTED)
    else:
        rendered = _value(entry.value, entry.key == "conn_str", secret_keys)
    return _key(entry.key) + " = " + rendered


def profile_toml(profile: Profile, secret_keys: CottList[str]) -> str:
    return "".join(_entry(entry, secret_keys) + "\n" for entry in profile.entries)
