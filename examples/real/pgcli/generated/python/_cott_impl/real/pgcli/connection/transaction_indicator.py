from real.pgcli.connection_types import TransactionStatus, TransactionStatus_Active, TransactionStatus_Idle, TransactionStatus_InError, TransactionStatus_InTransaction


def transaction_indicator(status: TransactionStatus) -> str:
    if isinstance(status, TransactionStatus_Idle):
        return ""
    if isinstance(status, (TransactionStatus_Active, TransactionStatus_InTransaction)):
        return "*"
    if isinstance(status, TransactionStatus_InError):
        return "!"
    return "?"
