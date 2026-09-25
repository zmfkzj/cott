package cott_impl.curriculum.fractional_range_values

internal fun build_bounded_range(start: kotlin.Double, stop: kotlin.Double, step: curriculum.fractional_range_values.PositiveStep, limit: curriculum.fractional_range_values.OutputLimit): cott_runtime.CottResult<cott_runtime.CottList<kotlin.Double>, curriculum.fractional_range_values.FractionalRangeError> {
    val stepValue: kotlin.Double = step.value
    if (!start.isFinite() || !stop.isFinite() || !stepValue.isFinite()) {
        return cott_runtime.Err(curriculum.fractional_range_values.FractionalRangeError.NonFiniteInput)
    }
    val values = kotlin.collections.ArrayList<kotlin.Double>()
    var index: kotlin.ULong = 0uL
    var previous: kotlin.Double = start
    while (true) {
        val product: kotlin.Double = index.toDouble() * stepValue
        val candidate: kotlin.Double = start + product
        if (!(candidate < stop)) {
            return cott_runtime.Ok(cott_runtime.CottList(values))
        }
        if (index == limit.value) {
            return cott_runtime.Err(curriculum.fractional_range_values.FractionalRangeError.OutputLimitExceeded)
        }
        if (index > 0uL && candidate <= previous) {
            return cott_runtime.Err(curriculum.fractional_range_values.FractionalRangeError.StepDoesNotAdvance)
        }
        values.add(candidate)
        previous = candidate
        index += 1uL
    }
}
