package cott_impl.curriculum.cta_row

internal fun decode_row(route: kotlin.String, date: kotlin.String, day_type: kotlin.String, rides: kotlin.Long): cott_runtime.CottResult<curriculum.cta_row.RideRow, curriculum.cta_row.RideRowError> {
    val day = when (day_type) {
        "U" -> curriculum.cta_row.DayType.SundayHoliday
        "A" -> curriculum.cta_row.DayType.Saturday
        "W" -> curriculum.cta_row.DayType.Weekday
        else -> return cott_runtime.Err(curriculum.cta_row.RideRowError.InvalidDayType)
    }
    if (rides < 0L) return cott_runtime.Err(curriculum.cta_row.RideRowError.InvalidRidership)
    if (!_validRoute(route)) return cott_runtime.Err(curriculum.cta_row.RideRowError.InvalidRoute)
    if (!_validDate(date)) return cott_runtime.Err(curriculum.cta_row.RideRowError.InvalidDate)
    return cott_runtime.Ok(
        curriculum.cta_row.RideRow(
            route = curriculum.cta_row.RouteCode(route),
            date = curriculum.cta_row.ServiceDate(date),
            day_type = day,
            rides = curriculum.cta_row.RideCount(rides.toULong())
        )
    )
}

private fun _validRoute(route: kotlin.String): kotlin.Boolean {
    if (route.length !in 1..4) return false
    var hasDigit = false
    for (character in route) {
        when (character) {
            in '0'..'9' -> hasDigit = true
            in 'A'..'Z' -> Unit
            else -> return false
        }
    }
    return hasDigit
}

private fun _validDate(date: kotlin.String): kotlin.Boolean {
    if (date.length != 10 || date[2] != '/' || date[5] != '/') return false
    for (index in date.indices) {
        if (index != 2 && index != 5 && date[index] !in '0'..'9') return false
    }
    val month = (date[0] - '0') * 10 + (date[1] - '0')
    val day = (date[3] - '0') * 10 + (date[4] - '0')
    val year = (date[6] - '0') * 1000 + (date[7] - '0') * 100 +
        (date[8] - '0') * 10 + (date[9] - '0')
    if (year == 0 || month !in 1..12) return false
    val daysInMonth = when (month) {
        2 -> if (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)) 29 else 28
        4, 6, 9, 11 -> 30
        else -> 31
    }
    return day in 1..daysInMonth
}
