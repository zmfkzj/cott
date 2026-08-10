from cott_runtime import CottList, Err, Ok, Result
from curriculum.expense_split_types import Balance, BalanceSheet, Expense, ExpenseSplitError, ExpenseSplitError_BlankPayer, ExpenseSplitError_DuplicateParticipant, ExpenseSplitError_EmptyParticipants, ExpenseSplitError_PayerNotParticipant, ExpenseSplitError_ZeroAmount


def calculate_balances(expense: Expense) -> Result[BalanceSheet, ExpenseSplitError]:
    """Validate an expense and calculate exact alphabetically ordered balances."""
    if len(expense.payer) == 0:
        return Err(error=ExpenseSplitError_BlankPayer())
    if len(expense.participants) == 0:
        return Err(error=ExpenseSplitError_EmptyParticipants())
    if expense.amount_cents == 0:
        return Err(error=ExpenseSplitError_ZeroAmount())

    seen: set[str] = set()
    for participant in expense.participants:
        if participant in seen:
            return Err(error=ExpenseSplitError_DuplicateParticipant())
        seen.add(participant)

    if expense.payer not in seen:
        return Err(error=ExpenseSplitError_PayerNotParticipant())

    participants: list[str] = sorted(expense.participants)
    participant_count: int = len(participants)
    share_cents: int = expense.amount_cents // participant_count
    remainder_cents: int = expense.amount_cents % participant_count
    debtors: list[Balance] = []
    creditors: list[Balance] = []

    for index, participant in enumerate(participants):
        owed_cents: int = share_cents + (1 if index < remainder_cents else 0)
        net_cents: int = (expense.amount_cents if participant == expense.payer else 0) - owed_cents
        if net_cents < 0:
            debtors.append(Balance(participant=participant, cents=-net_cents))
        elif net_cents > 0:
            creditors.append(Balance(participant=participant, cents=net_cents))

    return Ok(value=BalanceSheet(debtors=CottList(values=debtors), creditors=CottList(values=creditors)))
