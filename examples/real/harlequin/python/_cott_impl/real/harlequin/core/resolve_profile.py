from cott_runtime import CottList, Err, Ok, Result, Some
from real.harlequin.core_types import AdapterKind_DuckDb, CliOptions, Configuration, ConfigurationError, ConfigurationError_ProfileMissing, ConnectionRequest


def resolve_profile(configuration: Configuration, options: CliOptions) -> Result[ConnectionRequest, ConfigurationError]:
    name: str | None = None
    if isinstance(options.profile, Some):
        name = options.profile.value
    elif not options.no_config and isinstance(configuration.default_profile, Some):
        name = configuration.default_profile.value
    if name is None:
        request = ConnectionRequest(adapter=AdapterKind_DuckDb(), endpoint=":memory:", settings=CottList(values=[]), read_only=False)
    else:
        found: ConnectionRequest | None = None
        if not options.no_config:
            for profile in configuration.profiles:
                if profile.name == name:
                    found = ConnectionRequest(adapter=profile.adapter, endpoint=profile.endpoint, settings=profile.settings, read_only=profile.read_only)
                    break
        if found is None:
            return Err(error=ConfigurationError_ProfileMissing(name=name))
        request = found
    adapter = request.adapter
    if isinstance(options.adapter, Some):
        adapter = options.adapter.value
    endpoint = request.endpoint
    if isinstance(options.connection, Some):
        endpoint = options.connection.value
    return Ok(value=ConnectionRequest(adapter=adapter, endpoint=endpoint, settings=request.settings, read_only=request.read_only or options.read_only))
