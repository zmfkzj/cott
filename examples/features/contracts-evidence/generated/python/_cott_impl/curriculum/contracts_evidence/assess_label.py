from __future__ import annotations

from cott_runtime import Err, Nothing, Ok, Result
from curriculum.contracts_evidence_types import (
    AcceptedLabel,
    LabelAssessment,
    LabelEvidenceError,
    LabelEvidenceError_Missing,
    LabelEvidenceError_TooShort,
    LabelRequest,
)


def assess_label(request: LabelRequest) -> Result[LabelAssessment, LabelEvidenceError]:
    option = request.label
    if isinstance(option, Nothing):
        return Err(error=LabelEvidenceError_Missing())
    label = option.value
    if len(label) < request.minimum_length:
        return Err(error=LabelEvidenceError_TooShort(actual=label))
    return Ok(
        value=LabelAssessment(
            text=label,
            length=len(label),
            label=AcceptedLabel(value=label),
        )
    )
