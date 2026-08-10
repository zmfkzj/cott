from cott_runtime import CottList
from curriculum.expense_split_types import Balance, BalanceSheet, Settlement, Transfer


def settle_balances(balances: BalanceSheet) -> Settlement:
    """Greedily settle alphabetically ordered debtor and creditor balances."""
    debtors: list[Balance] = sorted(balances.debtors, key=lambda balance: balance.participant)
    creditors: list[Balance] = sorted(balances.creditors, key=lambda balance: balance.participant)
    transfers: list[Transfer] = []
    debtor_index: int = 0
    creditor_index: int = 0
    debtor_remaining: int = 0
    creditor_remaining: int = 0

    while debtor_index < len(debtors) and creditor_index < len(creditors):
        if debtor_remaining == 0:
            debtor_remaining = debtors[debtor_index].cents
            if debtor_remaining == 0:
                debtor_index += 1
                continue
        if creditor_remaining == 0:
            creditor_remaining = creditors[creditor_index].cents
            if creditor_remaining == 0:
                creditor_index += 1
                continue

        cents: int = min(debtor_remaining, creditor_remaining)
        transfers.append(
            Transfer(
                sender=debtors[debtor_index].participant,
                recipient=creditors[creditor_index].participant,
                cents=cents,
            )
        )
        debtor_remaining -= cents
        creditor_remaining -= cents
        if debtor_remaining == 0:
            debtor_index += 1
        if creditor_remaining == 0:
            creditor_index += 1

    return Settlement(transfers=CottList(values=transfers))
