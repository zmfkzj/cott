from cott_runtime import Err, Ok, Result
from curriculum.expense_split import calculate_balances, settle_balances
from curriculum.expense_split_types import Expense, ExpenseSplitError, Settlement


def settle_expense(expense: Expense) -> Result[Settlement, ExpenseSplitError]:
    balances = calculate_balances(expense)
    if isinstance(balances, Err):
        return Err(error=balances.error)
    return Ok(value=settle_balances(balances.value))
