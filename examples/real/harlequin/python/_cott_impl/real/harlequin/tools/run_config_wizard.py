import shlex
import sys
from pathlib import Path
from typing import Any, Callable, Final, cast

import questionary
from cott_runtime import CottList, Err, I64, Nothing, Option, Some
from real.harlequin.adapters import adapter_options
from real.harlequin.adapters_types import AdapterDescriptor, AdapterOption, AdapterSetting, OptionKind_Choice, OptionKind_Flag, OptionKind_Repeated, SettingValue, SettingValue_Flag, SettingValue_Text, SettingValue_Values
from real.harlequin.config import profile_toml, read_config_file, write_profile
from real.harlequin.config_types import ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Integer, ConfigValue_Real, ConfigValue_Text, Profile
from real.harlequin.tools import wizard_profile
from real.harlequin.tools_types import WizardAnswers

_NEW: Final[str] = "[Create a New Profile]"
_NO_DEFAULT: Final[str] = "[No default]"
_SPLIT_INSTRUCTION: Final[str] = "Separate items by a space. Quote a single item containing spaces."


def _answer(question: Any) -> object:
    value: object = cast(object, question.ask())
    if value is None:
        raise KeyboardInterrupt
    return value


def _string(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("Expected a text answer.")
    return value


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        raise TypeError("Expected a list of answers.")
    return [_string(item) for item in cast(list[object], value)]


def _validate(value: object, rule: str) -> bool | str:
    if not isinstance(value, str):
        return "Expected text."
    if rule == "path":
        return True if value.endswith(".toml") else "Must create a file with a .toml extension."
    if rule == "name":
        return True if value.strip() and value.strip() != "None" else "Cannot be empty or None"
    if rule == "required":
        return True if value.strip() else "Cannot be empty"
    if rule == "integer":
        try:
            int(value)
        except ValueError:
            return "Must be an integer."
    if rule == "float" and value.strip():
        try:
            float(value)
        except ValueError:
            return "Must be a number."
    if rule == "split":
        try:
            shlex.split(value)
        except ValueError as error:
            return str(error)
    return True


def _text(message: str, default: str, instruction: str, rule: str, secret: bool) -> str:
    sdk: Any = questionary
    validator: Callable[[object], bool | str] = lambda value: _validate(value, rule)
    if secret:
        question: Any = sdk.password(message, default=default, instruction=instruction or None, validate=validator)
    else:
        question = sdk.text(message, default=default, instruction=instruction or None, validate=validator)
    return _string(_answer(question))


def _select(message: str, choices: list[str], default: str) -> str:
    sdk: Any = questionary
    question: Any = sdk.select(message, choices=choices, default=default if default in choices else None)
    return _string(_answer(question))


def _confirm(message: str, default: bool) -> bool:
    sdk: Any = questionary
    value = _answer(sdk.confirm(message, default=default))
    if not isinstance(value, bool):
        raise TypeError("Expected a boolean answer.")
    return value


def _checkbox(message: str, choices: list[tuple[str, str]], checked: list[str]) -> list[str]:
    sdk: Any = questionary
    items: list[object] = [cast(object, sdk.Choice(title=label, value=value, checked=value in checked)) for label, value in choices]
    return _strings(_answer(sdk.checkbox(message, choices=items)))


def _path(default_path: Path) -> Path:
    sdk: Any = questionary
    validator: Callable[[object], bool | str] = lambda value: _validate(value, "path")
    question: Any = sdk.path("What config file do you want to create or update?", default=str(default_path), validate=validator)
    return Path(_string(_answer(question))).expanduser().absolute()


def _default(values: dict[str, ConfigValue], key: str, fallback: str) -> str:
    value = values.get(key)
    if isinstance(value, ConfigValue_Text):
        return value.value
    if isinstance(value, (ConfigValue_Integer, ConfigValue_Real)):
        return str(value.value)
    if isinstance(value, ConfigValue_Array):
        return shlex.join([item.value for item in value.values if isinstance(item, ConfigValue_Text)])
    return fallback


def _boolean(values: dict[str, ConfigValue], key: str, fallback: bool) -> bool:
    value = values.get(key)
    return value.value if isinstance(value, ConfigValue_Boolean) else fallback


def _keymaps(values: dict[str, ConfigValue]) -> list[str]:
    value = values.get("keymap_name")
    if isinstance(value, ConfigValue_Array):
        return [item.value for item in value.values if isinstance(item, ConfigValue_Text)]
    if isinstance(value, ConfigValue_Text):
        return [value.value]
    return ["vscode"]


def _option(option: AdapterOption, values: dict[str, ConfigValue]) -> AdapterSetting:
    key = option.name.replace("-", "_")
    default = _default(values, key, option.default.value if isinstance(option.default, Some) else "")
    kind = option.kind
    setting: SettingValue
    if isinstance(kind, OptionKind_Flag):
        setting = SettingValue_Flag(value=_confirm(option.label, _boolean(values, key, default.casefold() == "true")))
    elif isinstance(kind, OptionKind_Choice):
        choices = [item for item in kind.choices]
        normalized = next((item for item in choices if item.casefold() == default.casefold()), default)
        setting = SettingValue_Text(value=_select(option.label, choices, normalized))
    else:
        repeated = isinstance(kind, OptionKind_Repeated)
        answer = _text(option.label, default, option.description, "split" if repeated else "", option.secret)
        if repeated:
            setting = SettingValue_Values(values=CottList(values=shlex.split(answer)))
        else:
            setting = SettingValue_Text(value=answer)
    return AdapterSetting(name=key, value=setting)


def run_config_wizard(explicit_path: Option[Path], default_path: Path, descriptors: CottList[AdapterDescriptor], theme_names: CottList[str], keymap_names: CottList[str]) -> I64:
    try:
        if isinstance(explicit_path, Some):
            path = explicit_path.value
            print(f"Updating the file at {path}:")
        else:
            path = _path(default_path)
        if not str(path).endswith(".toml"):
            print("Harlequin could not create your configuration.", file=sys.stderr)
            print("Must create a file with a .toml extension.", file=sys.stderr)
            return 0

        loaded = read_config_file(path)
        if isinstance(loaded, Err):
            print(loaded.error.title, file=sys.stderr)
            print(loaded.error.message, file=sys.stderr)
            return 0
        profiles: list[Profile] = []
        default_profile: Option[str] = Nothing()
        if isinstance(loaded.value, Some):
            profiles = [profile for profile in loaded.value.value.profiles]
            default_profile = loaded.value.value.default_profile
        names = [profile.name for profile in profiles]
        selected = _select("Which profile would you like to update?", [_NEW, *names], _NEW) if profiles else _NEW
        values: dict[str, ConfigValue] = {}
        if selected == _NEW:
            name = _text("What would you like to name your profile?", "", "", "name", False).strip()
        else:
            name = selected
            for existing in profiles:
                if existing.name == name:
                    values = {entry.key: entry.value for entry in existing.entries}
                    break

        by_name = {descriptor.name: descriptor for descriptor in descriptors}
        adapter = _select("Which adapter should this profile use?", sorted(by_name), _default(values, "adapter", "duckdb"))
        descriptor = by_name[adapter]
        conn_str = _text("What connection string(s) should this profile use?", _default(values, "conn_str", ""), _SPLIT_INSTRUCTION, "split", False)
        read_only = _confirm("Should this profile connect read-only?", _boolean(values, "read_only", False)) if descriptor.implements_read_only else False
        theme = _select("What theme should this profile use?", [item for item in theme_names], _default(values, "theme", "harlequin"))
        maps = _checkbox("Which keymaps would you like to use?", [(item, item) for item in keymap_names], _keymaps(values))
        limit = _text("How many rows should each query fetch from the database?", _default(values, "limit", ""), "Leave blank for app defaults; enter -1 for no limit.", "", False)
        viewer = _text("How many rows should the Results Viewer hold?", _default(values, "viewer_max_rows", "100000"), "Enter -1 for no limit.", "integer", False)
        files = _text("Show local files from a directory? (Leave blank to hide)", _default(values, "show_files", ""), "", "", False)
        s3 = _text("Show cloud storage files?", _default(values, "show_s3", ""), "", "", False)
        locale = _text("What locale should Harlequin use for formatting numbers?", _default(values, "locale", ""), "Leave blank to use the system locale.", "", False)
        use_ssh = _confirm("Do you connect via SSH?", bool(_default(values, "ssh_host", "").strip()))
        host = ""
        forwards = ""
        batch = False
        timeout = ""
        if use_ssh:
            host = _text("What is the SSH destination?", _default(values, "ssh_host", ""), "", "required", False)
            forwards = _text("Which SSH forwards would you like to use?", _default(values, "ssh_forward", ""), _SPLIT_INSTRUCTION, "split", False)
            batch = _confirm("Use SSH BatchMode?", _boolean(values, "ssh_batch_mode", False))
            timeout = _text("How many seconds should Harlequin wait for the forwards?", _default(values, "ssh_timeout", ""), "", "float", False)

        options = adapter_options(descriptor.kind)
        chosen = _checkbox("Which of the following adapter options would you like to set?", [(option.label, option.name) for option in options], [option.name for option in options if option.name.replace("-", "_") in values])
        settings = [_option(option, values) for option in options if option.name in chosen]
        if name not in names:
            names.append(name)
        selected_default = _select("Would you like to set a default profile?", [_NO_DEFAULT, *names], default_profile.value if isinstance(default_profile, Some) else _NO_DEFAULT)
        new_default: Option[str] = Nothing() if selected_default == _NO_DEFAULT else Some(value=selected_default)
        answers = WizardAnswers(profile_name=name, adapter=adapter, conn_str=conn_str, read_only=read_only, theme=theme, keymap_names=CottList(values=maps), limit=limit, viewer_max_rows=viewer, show_files=files, show_s3=s3, locale=locale, use_ssh=use_ssh, ssh_host=host, ssh_forwards=forwards, ssh_batch_mode=batch, ssh_timeout=timeout, options=CottList(values=settings))
        profile = wizard_profile(answers, options)
        print(profile_toml(profile, CottList(values=[option.name.replace("-", "_") for option in options if option.secret])))
        if _confirm("Save this profile?", True):
            written = write_profile(path, profile, new_default)
            if isinstance(written, Err):
                print(written.error.title, file=sys.stderr)
                print(written.error.message, file=sys.stderr)
            else:
                print(f"Profile {name} written to {path}")
        return 0
    except KeyboardInterrupt:
        print("Cancelled config updates. No changes were made to any files.")
        return 0
