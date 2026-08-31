from cott_runtime import CottList, Err, Ok, Result
from real.pgcli_types import ConnectionError, ConnectionError_ProfileMissing, ConnectionProfile


def resolve_profile(name: str, profiles: CottList[ConnectionProfile]) -> Result[ConnectionProfile, ConnectionError]:
    for profile in profiles:
        if profile.name == name:
            return Ok(value=profile)
    return Err(error=ConnectionError_ProfileMissing(name=name))
