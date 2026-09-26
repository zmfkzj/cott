from cott_runtime import Err, Nothing, Ok, Option, Result, Some

from real.harlequin.config_types import ConfigError, ConfigError_Invalid, MergedConfig, Profile


def _lookup(merged: MergedConfig, name: str) -> Result[Option[Profile], ConfigError]:
    for profile in merged.profiles:
        if profile.name == name:
            return Ok(value=Some(value=profile))
    return Err(error=ConfigError_Invalid(title="Harlequin couldn't load your profile.", message=f"Could not load the profile named {name} because it does not exist in any discovered config files."))


def select_profile(merged: MergedConfig, requested: Option[str]) -> Result[Option[Profile], ConfigError]:
    if isinstance(requested, Some):
        if requested.value == "None":
            return Ok(value=Nothing())
        return _lookup(merged, requested.value)
    default = merged.default_profile
    if isinstance(default, Some):
        return _lookup(merged, default.value)
    return Ok(value=Nothing())
