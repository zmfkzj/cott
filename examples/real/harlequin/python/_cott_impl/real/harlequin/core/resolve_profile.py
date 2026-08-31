from cott_runtime import Err, Ok, Result, Some
from real.harlequin.core_types import (
    CliOptions,
    Configuration,
    ConfigurationError,
    ConfigurationError_ProfileMissing,
    ConnectionRequest,
)


def resolve_profile(configuration: Configuration, options: CliOptions) -> Result[ConnectionRequest, ConfigurationError]:
    if isinstance(options.profile, Some):
        profile_name = options.profile.value
    elif isinstance(configuration.default_profile, Some):
        profile_name = configuration.default_profile.value
    else:
        profile_name = ""

    for profile in configuration.profiles:
        if profile.name != profile_name:
            continue

        if isinstance(options.adapter, Some):
            adapter = options.adapter.value
        else:
            adapter = profile.adapter

        if isinstance(options.connection, Some):
            endpoint = options.connection.value
        else:
            endpoint = profile.endpoint

        return Ok(
            value=ConnectionRequest(
                adapter=adapter,
                endpoint=endpoint,
                settings=profile.settings,
                read_only=profile.read_only or options.read_only,
            )
        )

    return Err(error=ConfigurationError_ProfileMissing(name=profile_name))
