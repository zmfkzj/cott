package cott_impl.curriculum.contracts_evidence

internal fun assess_label(request: curriculum.contracts_evidence.LabelRequest): cott_runtime.CottResult<curriculum.contracts_evidence.LabelAssessment, curriculum.contracts_evidence.LabelEvidenceError> {
    val text = when (val label = request.label) {
        is cott_runtime.Some -> label.value
        cott_runtime.Nothing -> return cott_runtime.Err(curriculum.contracts_evidence.LabelEvidenceError.Missing)
    }
    val length = text.codePointCount(0, text.length).toULong()
    if (length < request.minimum_length) {
        return cott_runtime.Err(curriculum.contracts_evidence.LabelEvidenceError.TooShort(text))
    }
    return cott_runtime.Ok(
        curriculum.contracts_evidence.LabelAssessment(
            text = text,
            length = length,
            label = curriculum.contracts_evidence.AcceptedLabel(text)
        )
    )
}
