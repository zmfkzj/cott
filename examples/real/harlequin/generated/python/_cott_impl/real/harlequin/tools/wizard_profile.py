import shlex

from cott_runtime import CottList
from real.harlequin.adapters_types import AdapterOption, SettingValue_Flag, SettingValue_Text
from real.harlequin.config_types import ConfigEntry, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Integer, ConfigValue_Real, ConfigValue_Text, Profile
from real.harlequin.tools_types import WizardAnswers


def _nonnegative_int(text: str) -> int:
    try:
        return int(text.strip())
    except ValueError:
        return -1


def _text_array(texts: list[str]) -> ConfigValue_Array:
    return ConfigValue_Array(values=CottList(values=[ConfigValue_Text(value=text) for text in texts]))


def wizard_profile(answers: WizardAnswers, adapter_option_list: CottList[AdapterOption]) -> Profile:
    entries: list[ConfigEntry] = [ConfigEntry(key="adapter", value=ConfigValue_Text(value=answers.adapter))]
    if answers.conn_str.strip():
        entries.append(ConfigEntry(key="conn_str", value=_text_array(shlex.split(answers.conn_str))))
    if answers.read_only:
        entries.append(ConfigEntry(key="read_only", value=ConfigValue_Boolean(value=True)))
    entries.append(ConfigEntry(key="theme", value=ConfigValue_Text(value=answers.theme)))
    viewer_max_rows = _nonnegative_int(answers.viewer_max_rows)
    if viewer_max_rows >= 0:
        entries.append(ConfigEntry(key="viewer_max_rows", value=ConfigValue_Integer(value=viewer_max_rows)))
    entries.append(ConfigEntry(key="keymap_name", value=_text_array(list(answers.keymap_names))))
    limit = _nonnegative_int(answers.limit)
    if limit >= 0:
        entries.append(ConfigEntry(key="limit", value=ConfigValue_Integer(value=limit)))
    entries.append(ConfigEntry(key="show_files", value=ConfigValue_Text(value=answers.show_files)))
    entries.append(ConfigEntry(key="show_s3", value=ConfigValue_Text(value=answers.show_s3)))
    if answers.locale.strip():
        entries.append(ConfigEntry(key="locale", value=ConfigValue_Text(value=answers.locale)))
    if answers.use_ssh:
        entries.append(ConfigEntry(key="ssh_host", value=ConfigValue_Text(value=answers.ssh_host.strip())))
        if answers.ssh_forwards.strip():
            entries.append(ConfigEntry(key="ssh_forward", value=_text_array(shlex.split(answers.ssh_forwards))))
        if answers.ssh_batch_mode:
            entries.append(ConfigEntry(key="ssh_batch_mode", value=ConfigValue_Boolean(value=True)))
        if answers.ssh_timeout.strip():
            entries.append(ConfigEntry(key="ssh_timeout", value=ConfigValue_Real(value=float(answers.ssh_timeout))))
    settings = {setting.name: setting.value for setting in answers.options}
    for option in adapter_option_list:
        key = option.name.replace("-", "_")
        if key not in settings:
            continue
        value = settings[key]
        if isinstance(value, SettingValue_Text):
            if value.value.strip():
                entries.append(ConfigEntry(key=key, value=ConfigValue_Text(value=value.value)))
        elif isinstance(value, SettingValue_Flag):
            entries.append(ConfigEntry(key=key, value=ConfigValue_Boolean(value=value.value)))
        else:
            if value.values:
                entries.append(ConfigEntry(key=key, value=_text_array(list(value.values))))
    return Profile(name=answers.profile_name, entries=CottList(values=entries))
