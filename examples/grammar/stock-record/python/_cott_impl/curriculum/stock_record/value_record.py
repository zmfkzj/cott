from math import isfinite

from cott_runtime import Err, F64, Ok, Result
from curriculum.stock_record_types import StockRecord, StockRecordError, StockRecordError_ValuationOverflow


def value_record(record: StockRecord) -> Result[F64, StockRecordError]:
    value = record.shares * record.price
    if not isfinite(value):
        return Err(error=StockRecordError_ValuationOverflow())
    return Ok(value=value)
