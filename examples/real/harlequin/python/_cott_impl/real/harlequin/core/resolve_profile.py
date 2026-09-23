from cott_runtime import Err, Ok, Result, Some
from real.harlequin.core_types import CliOptions, Configuration, ConfigurationError, ConfigurationError_ProfileMissing, ConnectionRequest


def resolve_profile(configuration: Configuration, options: CliOptions) -> Result[ConnectionRequest, ConfigurationError]:
    name = ""
    if isinstance(options.profile, Some):
        name = options.profile.value
    elif isinstance(configuration.default_profile, Some):
        name = configuration.default_profile.value
    else:
        return Err(error=ConfigurationError_ProfileMissing(name=""))
    for profile in configuration.profiles:
        if profile.name == name:
            if len(profile.endpoint) == 0:
                return Err(error=ConfigurationError_ProfileMissing(name=name))
            return Ok(value=ConnectionRequest(adapter=profile.adapter, endpoint=profile.endpoint, settings=profile.settings, read_only=profile.read_only))
    return Err(error=ConfigurationError_ProfileMissing(name=name))
