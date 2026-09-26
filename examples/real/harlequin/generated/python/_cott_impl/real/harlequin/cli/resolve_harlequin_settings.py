from typing import Final

from cott_runtime import CottList, Err, F64, Nothing, Ok, Result, Some, U64, Option
from real.harlequin.sqltext import close_matches
from real.harlequin.adapters_types import AdapterDescriptor, AdapterOption, AdapterSetting, ConnectionRequest, OptionKind_Choice, OptionKind_Flag, OptionKind_Repeated, SettingValue, SettingValue_Flag, SettingValue_Text, SettingValue_Values
from real.harlequin.cli_types import CliArguments, HarlequinSettings, SshSettings
from real.harlequin.config_types import ConfigError, ConfigError_Invalid, ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Integer, ConfigValue_Real, ConfigValue_Text, Profile

_LOAD_TITLE: Final[str] = "Harlequin couldn't load your config file."
_START_TITLE: Final[str] = "Harlequin could not start."
_COMMAND_KEYS: Final[str] = "adapter conn_str read_only theme keymap_name limit viewer_max_rows output show_files show_s3 locale no_write_history no_download_tzdata ssh_host ssh_forward ssh_batch_mode ssh_allow_reuse ssh_timeout"


def _fail(title: str, message: str) -> Result[HarlequinSettings, ConfigError]:
    return Err(error=ConfigError_Invalid(title=title, message=message))


def _bad(key: str, adapter: str, reason: str) -> Result[HarlequinSettings, ConfigError]:
    return _fail(_LOAD_TITLE, f"Profile sets {key} to a value the {adapter} adapter cannot take: {reason}.")


def _raw(value: ConfigValue) -> object:
    if isinstance(value, ConfigValue_Text):
        return value.value
    if isinstance(value, ConfigValue_Integer):
        return value.value
    if isinstance(value, ConfigValue_Real):
        return value.value
    if isinstance(value, ConfigValue_Boolean):
        return value.value
    return value


def _as_bool(value: ConfigValue) -> bool | None:
    if isinstance(value, ConfigValue_Boolean):
        return value.value
    if isinstance(value, ConfigValue_Text):
        lowered = value.value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return None


def _as_text_list(value: ConfigValue) -> list[str] | None:
    if isinstance(value, ConfigValue_Text):
        return [value.value]
    if isinstance(value, ConfigValue_Array):
        out: list[str] = []
        for item in value.values:
            if not isinstance(item, ConfigValue_Text):
                return None
            out.append(item.value)
        return out
    return None


def _as_scalar_text(value: ConfigValue) -> str | None:
    if isinstance(value, ConfigValue_Text):
        return value.value
    if isinstance(value, ConfigValue_Integer):
        return str(value.value)
    if isinstance(value, ConfigValue_Real):
        return repr(value.value)
    return None


def _rows(key: str, value: ConfigValue, zero_is_none: bool) -> tuple[bool, int | None, str]:
    number: int | None = None
    if isinstance(value, ConfigValue_Integer):
        number = value.value
    elif isinstance(value, ConfigValue_Real):
        if value.value == value.value and value.value not in (float("inf"), float("-inf")) and value.value.is_integer():
            number = int(value.value)
    elif isinstance(value, ConfigValue_Text):
        try:
            number = int(value.value.strip())
        except ValueError:
            number = None
    if number is None:
        return (False, None, f"{key}={_raw(value)!r} is not a whole number of rows.")
    if number < -1:
        return (False, None, f"{key}={_raw(value)!r} is not a number of rows. Pass -1 for no limit.")
    if number == -1 or (zero_is_none and number == 0):
        return (True, None, "")
    return (True, number, "")


def _setting(option: AdapterOption, key: str, value: ConfigValue) -> SettingValue | str:
    kind = option.kind
    if isinstance(kind, OptionKind_Flag):
        flag = _as_bool(value)
        if flag is None:
            return "expected true or false"
        return SettingValue_Flag(value=flag)
    if isinstance(kind, OptionKind_Repeated):
        items = _as_text_list(value)
        if items is None:
            return "expected a list of strings"
        return SettingValue_Values(values=CottList(values=items))
    if isinstance(kind, OptionKind_Choice):
        if isinstance(value, ConfigValue_Text):
            for choice in kind.choices:
                if choice.lower() == value.value.lower():
                    return SettingValue_Text(value=choice)
        return "expected one of " + ", ".join(kind.choices)
    text = _as_scalar_text(value)
    if text is None:
        return "expected a string"
    return SettingValue_Text(value=text)


def resolve_harlequin_settings(profile: Option[Profile], arguments: CliArguments, descriptor: AdapterDescriptor, options: CottList[AdapterOption]) -> Result[HarlequinSettings, ConfigError]:
    adapter = descriptor.name
    merged: dict[str, ConfigValue] = {}
    from_cli: set[str] = set()
    profile_name: Option[str] = Nothing()
    if isinstance(profile, Some):
        profile_name = Some(value=profile.value.name)
        for entry in profile.value.entries:
            merged[entry.key] = entry.value
    for entry in arguments.explicit:
        merged[entry.key] = entry.value
        from_cli.add(entry.key)
    positional = [s for s in arguments.conn_str]
    if positional:
        merged["conn_str"] = ConfigValue_Array(values=CottList(values=[ConfigValue_Text(value=s) for s in positional]))

    by_key: dict[str, AdapterOption] = {}
    for option in options:
        by_key[option.name.replace("-", "_")] = option
    command_keys = _COMMAND_KEYS.split(" ")

    conn_str: list[str] = []
    read_only = False
    theme = "harlequin"
    keymaps: list[str] = ["vscode"]
    limit: int | None = None
    viewer: int | None = 100000
    texts: dict[str, str] = {}
    record_history = True
    download_tzdata = True
    ssh_host: str | None = None
    ssh_forward: list[str] = []
    ssh_batch = False
    ssh_reuse = False
    ssh_timeout = 60.0
    ssh_set = False
    settings: list[AdapterSetting] = []

    for key, value in merged.items():
        if key == "adapter":
            if not (isinstance(value, ConfigValue_Text) and value.value == adapter):
                return _bad(key, adapter, f"expected '{adapter}'")
        elif key == "conn_str":
            items = _as_text_list(value)
            if items is None:
                return _bad(key, adapter, "expected a string or a list of strings")
            conn_str = items
        elif key == "read_only":
            flag = _as_bool(value)
            if flag is None:
                return _bad(key, adapter, "expected true or false")
            read_only = flag
        elif key == "theme":
            if not isinstance(value, ConfigValue_Text):
                return _bad(key, adapter, "expected a string")
            theme = value.value
        elif key == "keymap_name":
            items = _as_text_list(value)
            if items is None:
                return _bad(key, adapter, "expected a string or a list of strings")
            keymaps = items
        elif key == "limit" or key == "viewer_max_rows":
            ok, rows, message = _rows(key, value, key == "viewer_max_rows")
            if not ok:
                return _fail(_LOAD_TITLE, message)
            if key == "limit":
                limit = rows
            else:
                viewer = rows
        elif key in ("output", "show_files", "show_s3", "locale", "ssh_host"):
            if not isinstance(value, ConfigValue_Text):
                return _bad(key, adapter, "expected a string")
            if key == "ssh_host":
                ssh_host = value.value
            else:
                texts[key] = value.value
        elif key == "no_write_history":
            if not isinstance(value, ConfigValue_Boolean):
                return _fail(_LOAD_TITLE, "no_write_history must be true or false.")
            record_history = not value.value
        elif key == "no_download_tzdata":
            if not isinstance(value, ConfigValue_Boolean):
                return _fail(_LOAD_TITLE, "no_download_tzdata must be true or false.")
            download_tzdata = not value.value
        elif key == "ssh_forward":
            items = _as_text_list(value)
            if items is None:
                return _bad(key, adapter, "expected a string or a list of strings")
            ssh_forward = items
            ssh_set = True
        elif key == "ssh_batch_mode":
            if not isinstance(value, ConfigValue_Boolean):
                return _bad(key, adapter, "expected true or false")
            ssh_batch = value.value
            ssh_set = True
        elif key == "ssh_allow_reuse":
            if not isinstance(value, ConfigValue_Boolean):
                return _bad(key, adapter, "expected true or false")
            if value.value and key not in from_cli:
                return _fail(_LOAD_TITLE, "ssh_allow_reuse can only be set on the command line. Pass --ssh-allow-reuse.")
            ssh_reuse = value.value
            ssh_set = True
        elif key == "ssh_timeout":
            seconds: float | None = None
            if isinstance(value, ConfigValue_Integer):
                seconds = float(value.value)
            elif isinstance(value, ConfigValue_Real):
                seconds = value.value
            if seconds is None or not seconds > 0 or seconds == float("inf"):
                return _fail(_LOAD_TITLE, f"{key}={_raw(value)!r} is not a positive number of seconds. Leave it out for a run that takes as long as it takes.")
            ssh_timeout = seconds
            ssh_set = True
        elif key in by_key:
            converted = _setting(by_key[key], key, value)
            if isinstance(converted, str):
                return _bad(key, adapter, converted)
            settings.append(AdapterSetting(name=key, value=converted))
        else:
            candidates = command_keys + list(by_key.keys())
            message = f"Profile defines an option '{key}', which is not an option of the {adapter} adapter."
            for match in close_matches(key, CottList(values=candidates), 1):
                message += f" Did you mean '{match}'?"
            return _fail(_LOAD_TITLE, message)

    if ssh_host is None and ssh_set:
        return _fail(_LOAD_TITLE, "SSH options are set but ssh_host is not.")
    if read_only and not descriptor.implements_read_only:
        return _fail(_START_TITLE, f"{adapter} does not declare read-only support, so --read-only cannot be honored. See `hsql --info`.")

    ssh: Option[SshSettings] = Nothing()
    if ssh_host is not None:
        timeout: F64 = ssh_timeout
        ssh = Some(value=SshSettings(host=ssh_host, forwards=CottList(values=ssh_forward), batch_mode=ssh_batch, allow_reuse=ssh_reuse, timeout_seconds=timeout))
    limit_opt: Option[U64] = Nothing() if limit is None else Some(value=limit)
    viewer_opt: Option[U64] = Nothing() if viewer is None else Some(value=viewer)
    request = ConnectionRequest(adapter=descriptor.kind, conn_str=CottList(values=conn_str), read_only=read_only, settings=CottList(values=settings))
    return Ok(value=HarlequinSettings(
        profile_name=profile_name,
        request=request,
        theme=theme,
        keymap_names=CottList(values=keymaps),
        limit=limit_opt,
        viewer_max_rows=viewer_opt,
        export_path=_opt(texts, "output"),
        show_files=_opt(texts, "show_files"),
        show_s3=_opt(texts, "show_s3"),
        locale=_opt(texts, "locale"),
        record_history=record_history,
        download_tzdata=download_tzdata,
        ssh=ssh,
    ))


def _opt(texts: dict[str, str], key: str) -> Option[str]:
    if key in texts:
        return Some(value=texts[key])
    return Nothing()
