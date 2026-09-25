from cott_runtime import Err, F64, Result
from curriculum.stock_record import value_record
from curriculum.stock_record_types import MAX_F64, StockRecord, StockRecordError, StockRecordError_EmptyName, StockRecordError_NegativePrice, StockRecordError_NegativeShares, StockRecordError_NonFinitePrice


def value_stock_record(record: StockRecord) -> Result[F64, StockRecordError]:
    if len(record.name) == 0:
        return Err(error=StockRecordError_EmptyName())
    if record.shares < 0:
        return Err(error=StockRecordError_NegativeShares())
    if not (-MAX_F64 <= record.price <= MAX_F64):
        return Err(error=StockRecordError_NonFinitePrice())
    if record.price < 0:
        return Err(error=StockRecordError_NegativePrice())
    return value_record(record)
