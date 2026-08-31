from cott_runtime import Err, Ok, Result
from real.yt_dlp_types import (
    CertificatePolicy_Insecure,
    CertificatePolicy_Verify,
    MediaError,
    MediaError_CertificateFailure,
    MediaError_WorkaroundRejected,
    WorkaroundPolicy,
)


def validate_workarounds(policy: WorkaroundPolicy) -> Result[WorkaroundPolicy, MediaError]:
    match policy.certificate:
        case CertificatePolicy_Insecure():
            if policy.legacy_server_connect:
                return Err(
                    error=MediaError_CertificateFailure(
                        message="insecure certificates cannot be combined with legacy server connections"
                    )
                )
        case CertificatePolicy_Verify():
            if policy.force_generic_extractor and policy.legacy_server_connect:
                return Err(
                    error=MediaError_WorkaroundRejected(
                        message="generic extractor and legacy server connection cannot be combined"
                    )
                )

    extractor_arg: str
    extractor: str
    separator: str
    arguments: str
    for extractor_arg in policy.extractor_args:
        extractor, separator, arguments = extractor_arg.partition(":")
        if separator == "" or extractor == "" or arguments == "":
            return Err(
                error=MediaError_WorkaroundRejected(
                    message="extractor arguments must use EXTRACTOR:ARGUMENTS syntax"
                )
            )

    return Ok(value=policy)
