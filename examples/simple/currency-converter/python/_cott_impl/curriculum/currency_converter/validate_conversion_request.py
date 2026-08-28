from cott_runtime import Err, F64, Ok, Result, UNIT, Unit
from curriculum.currency_converter_types import ConversionRequest, CurrencyError, CurrencyError_DuplicateRate, CurrencyError_InvalidCurrencyCode, CurrencyError_MissingRate, CurrencyError_NegativeQuantity, CurrencyError_NonFiniteQuantity, CurrencyError_NonFiniteRate, CurrencyError_NonPositiveRate


def _is_finite(value: F64) -> bool:
    infinity: F64 = float("inf")
    return -infinity < value < infinity


def _is_currency_code(code: str) -> bool:
    return len(code) == 3 and all("A" <= character <= "Z" for character in code)


def validate_conversion_request(request: ConversionRequest) -> Result[Unit, CurrencyError]:
    if not _is_finite(request.quantity):
        return Err(error=CurrencyError_NonFiniteQuantity())
    if request.quantity < 0.0:
        return Err(error=CurrencyError_NegativeQuantity())
    if not _is_currency_code(request.from_currency):
        return Err(error=CurrencyError_InvalidCurrencyCode())
    if not _is_currency_code(request.to_currency):
        return Err(error=CurrencyError_InvalidCurrencyCode())

    seen: set[str] = set()
    for rate in request.eur_rates:
        if not _is_currency_code(rate.code):
            return Err(error=CurrencyError_InvalidCurrencyCode())
        if not _is_finite(rate.per_eur):
            return Err(error=CurrencyError_NonFiniteRate())
        if rate.per_eur <= 0.0:
            return Err(error=CurrencyError_NonPositiveRate())
        if rate.code in seen:
            return Err(error=CurrencyError_DuplicateRate())
        seen.add(rate.code)

    if request.from_currency not in seen:
        return Err(error=CurrencyError_MissingRate())
    if request.to_currency not in seen:
        return Err(error=CurrencyError_MissingRate())
    return Ok(value=UNIT)
