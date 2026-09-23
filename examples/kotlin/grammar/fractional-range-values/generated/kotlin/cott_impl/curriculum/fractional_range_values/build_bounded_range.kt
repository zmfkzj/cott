package cott_impl.curriculum.fractional_range_values

internal fun build_bounded_range(start: kotlin.Double, stop: kotlin.Double, step: curriculum.fractional_range_values.PositiveStep, limit: curriculum.fractional_range_values.OutputLimit): cott_runtime.CottResult<cott_runtime.CottList<kotlin.Double>, curriculum.fractional_range_values.FractionalRangeError> {
    if (!start.isFinite() || !stop.isFinite() || !step.value.isFinite()) {
        return cott_runtime.Err(curriculum.fractional_range_values.FractionalRangeError.NonFiniteInput)
    }
    if (start >= stop) {
        return cott_runtime.Ok(cott_runtime.CottList(emptyList<kotlin.Double>()))
    }
    val values = kotlin.collections.ArrayList<kotlin.Double>()
    var index = 0u
    var previous = start
    while (true) {
        val candidate = start + index.toDouble() * step.value
        if (candidate >= stop) {
            return cott_runtime.Ok(cott_runtime.CottList(values))
        }
        if (index == limit.value) {
            return cott_runtime.Err(curriculum.fractional_range_values.FractionalRangeError.OutputLimitExceeded)
        }
        if (index > 0u && candidate <= previous) {
            return cott_runtime.Err(curriculum.fractional_range_values.FractionalRangeError.StepDoesNotAdvance)
        }
        values.add(candidate)
        previous = candidate
        index += 1u
    }
}
