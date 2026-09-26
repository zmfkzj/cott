from cott_runtime import CottList, Nothing, Option, Some

from real.harlequin.config_types import ConfigFile, MergedConfig, Profile, ProfileSource
from real.harlequin.keymap_types import KeyMap


def merge_config_files(files: CottList[ConfigFile]) -> MergedConfig:
    default_profile: Option[str] = Nothing()
    default_source: Option[str] = Nothing()
    profiles: list[Profile] = []
    keymaps: list[KeyMap] = []
    sources: list[ProfileSource] = []
    seen_profiles: set[str] = set()
    seen_keymaps: set[str] = set()
    for file in files:
        if isinstance(default_profile, Nothing):
            candidate = file.default_profile
            if isinstance(candidate, Some):
                default_profile = Some(value=candidate.value)
                default_source = Some(value=file.path)
        for profile in file.profiles:
            if profile.name not in seen_profiles:
                seen_profiles.add(profile.name)
                profiles.append(profile)
                sources.append(ProfileSource(name=profile.name, path=file.path))
        for keymap in file.keymaps:
            if keymap.name not in seen_keymaps:
                seen_keymaps.add(keymap.name)
                keymaps.append(keymap)
    return MergedConfig(
        default_profile=default_profile,
        default_source=default_source,
        profiles=CottList(values=profiles),
        keymaps=CottList(values=keymaps),
        sources=CottList(values=sources),
    )
