from cott_runtime import Err, Ok, Result, Some
from curriculum.contracts_evidence_types import AcceptedLabel, LabelAssessment, LabelEvidenceError, LabelEvidenceError_Missing, LabelEvidenceError_TooShort, LabelRequest


def assess_label(request: LabelRequest) -> Result[LabelAssessment, LabelEvidenceError]:
    label = request.label
    if not isinstance(label, Some):
        return Err(error=LabelEvidenceError_Missing())
    text: str = label.value
    length = len(text)
    if length < request.minimum_length:
        return Err(error=LabelEvidenceError_TooShort(actual=text))
    return Ok(value=LabelAssessment(text=text, length=length, label=AcceptedLabel(value=text)))
