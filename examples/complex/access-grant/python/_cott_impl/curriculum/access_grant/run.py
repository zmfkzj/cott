from cott_runtime import Ok, Result
from curriculum.access_grant_types import AccessError, AccessGrant, AccessGrant_Granted


def run() -> Result[AccessGrant, AccessError]:
    return Ok(value=AccessGrant_Granted())
