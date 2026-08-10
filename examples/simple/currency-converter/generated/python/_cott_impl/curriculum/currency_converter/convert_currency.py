from cott_runtime import Err, F64, Ok, Result
from curriculum.currency_converter import validate_conversion_request
from curriculum.currency_converter_types import ConversionRequest, CurrencyError, CurrencyError_NonFiniteResult


def convert_currency(request: ConversionRequest) -> Result[F64, CurrencyError]:
    validation = validate_conversion_request(request)
    if isinstance(validation, Err):
        return Err(error=validation.error)

    infinity: F64 = float("inf")

    def is_finite(value: F64) -> bool:
        return -infinity < value < infinity

    def round_to_cents(value: F64) -> F64:
        if value >= 140_737_488_355_328.0:
            return value
        ratio: tuple[int, int] = value.as_integer_ratio()
        numerator: int = ratio[0] * 100
        denominator: int = ratio[1]
        hundredths: int = numerator // denominator
        remainder: int = numerator % denominator
        if remainder * 2 > denominator or (remainder * 2 == denominator and hundredths % 2 != 0):
            hundredths += 1
        return hundredths / 100.0

    quantity: F64 = request.quantity
    if request.from_currency == request.to_currency:
        return Ok(value=round_to_cents(quantity))

    source_rate: F64 = 0.0
    destination_rate: F64 = 0.0
    for rate in request.eur_rates:
        if rate.code == request.from_currency:
            source_rate = rate.per_eur
        elif rate.code == request.to_currency:
            destination_rate = rate.per_eur

    intermediate: F64 = quantity / source_rate
    if not is_finite(intermediate):
        return Err(error=CurrencyError_NonFiniteResult())

    converted: F64 = intermediate * destination_rate
    if not is_finite(converted):
        return Err(error=CurrencyError_NonFiniteResult())

    return Ok(value=round_to_cents(converted))
