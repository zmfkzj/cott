import cott_runtime
from cott_runtime import Result
from real.yt_dlp_types import CertificatePolicy_Insecure, CertificatePolicy_Verify, MediaError, MediaError_CertificateFailure, MediaError_WorkaroundRejected, WorkaroundPolicy


def validate_workarounds(policy: WorkaroundPolicy) -> Result[WorkaroundPolicy, MediaError]:
    match policy.certificate:
        case CertificatePolicy_Insecure():
            return cott_runtime.Err(error=MediaError_CertificateFailure(message="insecure TLS is not supported; certificates are always verified"))
        case CertificatePolicy_Verify():
            if policy.legacy_server_connect:
                return cott_runtime.Err(error=MediaError_WorkaroundRejected(message="legacy TLS server connect is not supported"))
            if len(policy.extractor_args) > 0:
                return cott_runtime.Err(error=MediaError_WorkaroundRejected(message="extractor arguments are not supported by the generic extractor"))
            return cott_runtime.Ok(value=policy)
