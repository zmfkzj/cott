from cott_runtime import CottList, Some

from real.harlequin.adapters_types import AdapterOption, OptionKind_Choice, OptionKind_Flag, OptionKind_Repeated
from real.harlequin.config_types import AdapterOptionSet, ConfigFile, ConfigProblem, ConfigValue, ConfigValue_Array, ConfigValue_Boolean, ConfigValue_Integer, ConfigValue_Real, ConfigValue_Text
from real.harlequin.sqltext import close_matches


def _key_of(option: AdapterOption) -> str:
    return option.name.replace("-", "_")


def _type_reason(option: AdapterOption, value: ConfigValue) -> str | None:
    kind = option.kind
    if isinstance(kind, OptionKind_Flag):
        if isinstance(value, ConfigValue_Boolean):
            return None
        if isinstance(value, ConfigValue_Text) and value.value.lower() in ("true", "false"):
            return None
        return "expected a boolean"
    if isinstance(kind, OptionKind_Repeated):
        if isinstance(value, ConfigValue_Array):
            for item in value.values:
                if not isinstance(item, ConfigValue_Text):
                    return "expected an array of strings"
            return None
        return "expected an array of strings"
    if isinstance(kind, OptionKind_Choice):
        if isinstance(value, ConfigValue_Text):
            wanted = value.value.lower()
            for choice in kind.choices:
                if choice.lower() == wanted:
                    return None
        return "expected one of " + ", ".join(kind.choices)
    if isinstance(value, (ConfigValue_Text, ConfigValue_Integer, ConfigValue_Real)):
        return None
    return "expected a string or a number"


def _render(value: ConfigValue) -> str:
    if isinstance(value, ConfigValue_Text):
        return value.value
    if isinstance(value, ConfigValue_Boolean):
        return "true" if value.value else "false"
    if isinstance(value, (ConfigValue_Integer, ConfigValue_Real)):
        return str(value.value)
    return "..."


def validate_config_file(file: ConfigFile, options_of: CottList[AdapterOptionSet], command_keys: CottList[str], builtin_keymaps: CottList[str]) -> CottList[ConfigProblem]:
    problems: list[ConfigProblem] = []
    commands: list[str] = [key for key in command_keys]
    for profile in file.profiles:
        adapter = "duckdb"
        adapter_ok = True
        for entry in profile.entries:
            if entry.key == "adapter":
                value = entry.value
                named = value.value if isinstance(value, ConfigValue_Text) else None
                if named is None or not any(s.adapter == named for s in options_of):
                    shown = named if named is not None else _render(value)
                    problems.append(ConfigProblem(path=file.path, key=Some(value="profiles." + profile.name + ".adapter"), message="Profile sets adapter to '" + shown + "', which is not an installed adapter."))
                    adapter_ok = False
                else:
                    adapter = named
        if not adapter_ok:
            continue
        options: dict[str, AdapterOption] = {}
        for option_set in options_of:
            if option_set.adapter == adapter:
                for option in option_set.options:
                    options[_key_of(option)] = option
                break
        candidates = CottList(values=commands + list(options.keys()))
        unknown = sorted({e.key for e in profile.entries if e.key not in commands and e.key not in options})
        for key in unknown:
            message = "Profile defines an option '" + key + "', which is not an option of the " + adapter + " adapter."
            for suggestion in close_matches(key, candidates, 1):
                message += " Did you mean '" + suggestion + "'?"
                break
            problems.append(ConfigProblem(path=file.path, key=Some(value="profiles." + profile.name + "." + key), message=message))
        for entry in profile.entries:
            if entry.key in commands or entry.key not in options:
                continue
            reason = _type_reason(options[entry.key], entry.value)
            if reason is not None:
                problems.append(ConfigProblem(path=file.path, key=Some(value="profiles." + profile.name + "." + entry.key), message="Profile sets " + entry.key + " to a value the " + adapter + " adapter cannot take: " + reason + "."))
    for keymap in file.keymaps:
        for name in builtin_keymaps:
            if name == keymap.name:
                problems.append(ConfigProblem(path=file.path, key=Some(value="keymaps." + keymap.name), message="Keymap " + keymap.name + " is already defined by a plug-in; define a new name and load both maps."))
                break
    return CottList(values=problems)
